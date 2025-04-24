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
    if not query_text:
        return []
        
    # Clean up the query text
    query_text = clean_query(query_text)
    
    # See if we have this search cached
    cache_key = _generate_cache_key(
        query_text=query_text, 
        model_name=model_class.__name__ if model_class else 'all',
        additional_filters=additional_filters,
        order_by=order_by
    )
    
    cached_results = cache.get(cache_key)
    if cached_results is not None:
        logger.debug(f"Search cache hit for '{query_text}'")
        return cached_results
    
    results = []
    search_terms = query_text.split()
    
    # Determine which models to search
    if model_class:
        # Search specific model
        app_label = model_class._meta.app_label
        model_name = model_class._meta.model_name
        if (app_label, model_name) not in _SEARCH_REGISTRY:
            logger.warning(f"Model {model_class.__name__} not registered for search")
            return []
        models_to_search = {(app_label, model_name): _SEARCH_REGISTRY[(app_label, model_name)]}
    else:
        # Search all registered models
        models_to_search = _SEARCH_REGISTRY
    
    # Perform search on each registered model
    for (app_label, model_name), config in models_to_search.items():
        model = config['model']
        fields = config['fields']
        
        # Build query for each search term and field
        q_objects = []
        
        for term in search_terms:
            term_queries = []
            for field in fields:
                # Apply different lookup depending on field type
                field_obj = model._meta.get_field(field)
                lookup = 'iexact' if field_obj.get_internal_type() == 'CharField' and len(term) <= 15 else 'icontains'
                
                term_queries.append(Q(**{f"{field}__{lookup}": term}))
            
            # Combine field queries with OR for this term
            if term_queries:
                q_objects.append(reduce(or_, term_queries))
        
        # Combine term queries with AND
        if q_objects:
            query = reduce(lambda x, y: x & y, q_objects)
            
            # Add any additional filters
            if additional_filters:
                for key, value in additional_filters.items():
                    query &= Q(**{key: value})
            
            # Execute the query
            queryset = model.objects.filter(query)
            
            # Apply sorting if specified
            if order_by:
                queryset = queryset.order_by(order_by)
            
            # Limit results
            results.extend(queryset[:limit])
    
    # Cache the results
    cache.set(cache_key, results, SEARCH_CACHE_TIMEOUT)
    
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