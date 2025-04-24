# backend/root/services/search_service.py

import logging
from django.db.models import Q
from functools import reduce
from operator import or_
from django.conf import settings
import re
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Configuration
SEARCH_CACHE_TIMEOUT = getattr(settings, 'SEARCH_CACHE_TIMEOUT', 60 * 60)  # 1 hour default
ENABLE_ADVANCED_SEARCH = getattr(settings, 'ENABLE_ADVANCED_SEARCH', False)
MAX_SEARCH_RESULTS = getattr(settings, 'MAX_SEARCH_RESULTS', 100)

# Dictionary to track models registered for search
_SEARCH_REGISTRY = {}

def register_search_models(model_class, fields=None, boost_fields=None, analyzer=None):
    """
    Register a model for search indexing.
    
    Args:
        model_class (Model): The Django model class to register
        fields (list): List of field names to include in search
        boost_fields (dict): Dictionary mapping field names to boost values
        analyzer (callable): Optional function to pre-process field data for search
    """
    app_label = model_class._meta.app_label
    model_name = model_class._meta.model_name
    
    if not fields:
        # Default to using common text fields if none specified
        fields = [f.name for f in model_class._meta.fields 
                 if f.get_internal_type() in ('CharField', 'TextField')]
    
    # Store the registration
    _SEARCH_REGISTRY[(app_label, model_name)] = {
        'model': model_class,
        'fields': fields,
        'boost_fields': boost_fields or {},
        'analyzer': analyzer
    }
    
    logger.info(f"Registered {model_class.__name__} for search with fields: {fields}")
    return True

def perform_search(query_text, model_class=None, additional_filters=None, 
                  order_by=None, limit=MAX_SEARCH_RESULTS):
    """
    Search registered models for the given query.
    
    Args:
        query_text (str): The search query text
        model_class (Model, optional): Specific model to search, or None for all registered models
        additional_filters (dict, optional): Additional filters to apply to query
        order_by (str, optional): Field to order results by
        limit (int, optional): Maximum number of results to return
        
    Returns:
        list: List of objects matching the search query
    """
    # Input validation
    if not query_text:
        logger.debug("Empty search query, returning empty results")
        return []
    
    # Enforce reasonable limits to prevent performance issues
    limit = min(limit or MAX_SEARCH_RESULTS, MAX_SEARCH_RESULTS)
    
    # Clean up the query text
    try:
        query_text = clean_query(query_text)
        logger.debug(f"Cleaned search query: '{query_text}'")
    except Exception as e:
        logger.error(f"Error cleaning query: {str(e)}")
        query_text = query_text.lower().strip()
    
    # Generate a simpler cache key
    try:
        model_identifier = f"{model_class.__name__}" if model_class else "all"
        filter_str = "_".join(f"{k}:{v}" for k, v in sorted(additional_filters.items())) if additional_filters else ""
        cache_key = f"search:{model_identifier}:{query_text}:{filter_str}:{order_by or ''}:{limit}"
        
        # Check cache
        cached_results = cache.get(cache_key)
        if cached_results is not None:
            logger.debug(f"Search cache hit for '{query_text}' - returning {len(cached_results)} results")
            return cached_results
    except Exception as e:
        logger.error(f"Error with cache handling: {str(e)}")
        # Continue with search even if caching fails
    
    # Split search terms
    search_terms = query_text.split()
    logger.debug(f"Search terms: {search_terms}")
    
    # Find models to search
    try:
        # Determine which models to search
        if model_class:
            # Search specific model
            app_label = model_class._meta.app_label
            model_name = model_class._meta.model_name
            
            if (app_label, model_name) not in _SEARCH_REGISTRY:
                logger.warning(f"Model {model_class.__name__} not registered for search")
                # Use fallback approach - common text fields
                fields = ['common_name', 'scientific_name', 'description', 'name', 'title']
                models_to_search = {(app_label, model_name): {
                    'model': model_class,
                    'fields': [f for f in fields if hasattr(model_class, f)],
                    'boost_fields': {}
                }}
            else:
                models_to_search = {(app_label, model_name): _SEARCH_REGISTRY[(app_label, model_name)]}
        else:
            # Search all registered models
            models_to_search = _SEARCH_REGISTRY
            
        logger.debug(f"Searching in models: {[m['model'].__name__ for m in models_to_search.values()]}")
    except Exception as e:
        logger.error(f"Error setting up search models: {str(e)}")
        return []
    
    results = []
    
    # Search each model
    for (app_label, model_name), config in models_to_search.items():
        try:
            model = config['model']
            fields = config['fields']
            
            if not fields:
                logger.warning(f"No search fields for {model.__name__}")
                continue
                
            logger.debug(f"Searching {model.__name__} in fields: {fields}")
            
            # Build a simpler query
            query_filters = Q()
            
            # For each search term, look in all fields with OR relationship
            for term in search_terms:
                term_filter = Q()
                for field in fields:
                    try:
                        # Just use icontains for simplicity and reliability
                        term_filter |= Q(**{f"{field}__icontains": term})
                    except Exception as e:
                        logger.warning(f"Error adding field {field} to search: {str(e)}")
            
                # Add this term's filter with AND relationship
                query_filters &= term_filter
            
            # Base queryset
            queryset = model.objects.all()
            
            # Apply the search filter
            if query_filters:
                queryset = queryset.filter(query_filters)
            
            # Add any additional filters
            if additional_filters:
                try:
                    valid_filters = {}
                    for key, value in additional_filters.items():
                        if key in [f.name for f in model._meta.fields]:
                            valid_filters[key] = value
                            
                    if valid_filters:
                        queryset = queryset.filter(**valid_filters)
                except Exception as e:
                    logger.error(f"Error applying additional filters: {str(e)}")
            
            # Apply sorting if specified
            if order_by:
                try:
                    queryset = queryset.order_by(order_by)
                except Exception as e:
                    logger.warning(f"Invalid order_by parameter: {str(e)}")
            
            # Avoid processing huge result sets - use efficient pagination approach
            queryset = queryset[:limit]
            
            # Execute the query and get results
            model_results = list(queryset)
            results.extend(model_results)
            logger.info(f"Found {len(model_results)} results from {model.__name__}")
            
        except Exception as e:
            logger.error(f"Error searching {app_label}.{model_name}: {str(e)}")
    
    # Limit final combined results
    results = results[:limit]
    
    # Try to cache results
    try:
        if results and cache_key:
            cache.set(cache_key, results, SEARCH_CACHE_TIMEOUT)
    except Exception as e:
        logger.error(f"Error caching search results: {str(e)}")
    
    logger.info(f"Search for '{query_text}' found {len(results)} total results")
    return results

def clean_query(query_text):
    """Clean and normalize a search query."""
    # Remove special characters
    query_text = re.sub(r'[^\w\s]', ' ', query_text)
    # Normalize whitespace
    query_text = re.sub(r'\s+', ' ', query_text).strip().lower()
    return query_text

def _generate_cache_key(query_text, model_name, additional_filters, order_by):
    """Generate a cache key for search results."""
    key_parts = [
        'search',
        model_name,
        query_text
    ]
    
    if additional_filters:
        # Sort to ensure consistent ordering of filter items
        filter_str = '_'.join(f"{k}:{v}" for k, v in sorted(additional_filters.items()))
        key_parts.append(filter_str)
        
    if order_by:
        key_parts.append(f"order:{order_by}")
        
    return ':'.join(key_parts)

def reindex_model(model_class, instance_ids=None):
    """
    Reindex a model or specific instances.
    
    Args:
        model_class (Model): The model to reindex
        instance_ids (list, optional): IDs of specific instances to reindex
    """
    app_label = model_class._meta.app_label
    model_name = model_class._meta.model_name
    
    if (app_label, model_name) not in _SEARCH_REGISTRY:
        logger.warning(f"Model {model_class.__name__} not registered for search")
        return False
    
    if ENABLE_ADVANCED_SEARCH:
        try:
            from services.external_search import index_objects
            
            config = _SEARCH_REGISTRY[(app_label, model_name)]
            
            if instance_ids:
                objects = model_class.objects.filter(id__in=instance_ids)
            else:
                objects = model_class.objects.all()
                
            # Index the objects
            index_objects(
                model_class=model_class,
                objects=objects,
                fields=config['fields'],
                boost_fields=config['boost_fields']
            )
            logger.info(f"Reindexed {objects.count()} {model_class.__name__} objects")
        except ImportError:
            logger.warning("External search service not available")
            return False
    else:
        # When using Django's built-in search, we don't need to manually index
        # We just need to clear any cached search results
        cache_keys = cache.keys('search:*')
        if cache_keys:
            cache.delete_many(cache_keys)
            logger.info(f"Cleared search cache for {model_class.__name__}")
    
    return True

def get_search_suggestions(prefix, model_class=None, field='common_name', limit=10):
    """
    Get autocomplete suggestions starting with the given prefix.
    
    Args:
        prefix (str): The prefix to suggest completions for
        model_class (Model, optional): Model to get suggestions from
        field (str): Field to get suggestions from
        limit (int): Maximum number of suggestions
        
    Returns:
        list: List of suggestion strings
    """
    if not prefix or len(prefix) < 2:
        return []
    
    # Clean the prefix
    prefix = clean_query(prefix)
    
    # Determine which models to search
    if model_class:
        app_label = model_class._meta.app_label
        model_name = model_class._meta.model_name
        if (app_label, model_name) not in _SEARCH_REGISTRY:
            return []
        models_to_search = {(app_label, model_name): _SEARCH_REGISTRY[(app_label, model_name)]}
    else:
        # Use the first registered model that has the requested field
        models_to_search = {}
        for key, config in _SEARCH_REGISTRY.items():
            if field in config['fields']:
                models_to_search[key] = config
                break
    
    suggestions = []
    for (app_label, model_name), config in models_to_search.items():
        model = config['model']
        
        # Check if the field is valid
        if field not in config['fields']:
            logger.warning(f"Field '{field}' not in search fields for {model.__name__}")
            continue
            
        # Get suggestions from the database
        query = {f"{field}__istartswith": prefix}
        qs = model.objects.filter(**query).values_list(field, flat=True).distinct()
        suggestions.extend(qs[:limit])
    
    return suggestions[:limit]