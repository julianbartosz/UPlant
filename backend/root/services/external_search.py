# backend/root/services/external_search.py

import logging
import json
from django.conf import settings
from django.db.models import Model
from typing import List, Dict, Any, Optional, Type, Union
import uuid

logger = logging.getLogger(__name__)

# Configuration from settings
ELASTICSEARCH_HOSTS = getattr(settings, 'ELASTICSEARCH_HOSTS', ['http://localhost:9200'])
ELASTICSEARCH_INDEX_PREFIX = getattr(settings, 'ELASTICSEARCH_INDEX_PREFIX', 'uplant')
SEARCH_SETTINGS = getattr(settings, 'SEARCH_SETTINGS', {})

class SearchEngineError(Exception):
    """Base exception for search engine errors"""
    pass

class ElasticsearchEngine:
    """Elasticsearch implementation of the search engine"""
    
    def __init__(self):
        self.initialized = False
        
    def initialize(self):
        """Initialize Elasticsearch client"""
        try:
            from elasticsearch import Elasticsearch
            
            # Create Elasticsearch client
            self.client = Elasticsearch(
                ELASTICSEARCH_HOSTS,
                **SEARCH_SETTINGS.get('elasticsearch', {})
            )
            
            # Check connection
            if not self.client.ping():
                raise SearchEngineError("Unable to connect to Elasticsearch")
                
            self.initialized = True
            logger.info("Elasticsearch client initialized successfully")
        except ImportError:
            raise SearchEngineError("Elasticsearch package not installed. "
                                   "Install with 'pip install elasticsearch'")
        except Exception as e:
            raise SearchEngineError(f"Failed to initialize Elasticsearch: {e}")
    
    def ensure_initialized(self):
        """Ensure the search engine is initialized"""
        if not self.initialized:
            self.initialize()
            
    def create_index(self, index_name: str, mapping: Dict[str, Any] = None) -> bool:
        """Create an Elasticsearch index with optional mapping"""
        self.ensure_initialized()
        
        try:
            # Check if index already exists
            if self.client.indices.exists(index=index_name):
                logger.info(f"Index {index_name} already exists")
                return True
                
            # Create index with mapping if provided
            if mapping:
                self.client.indices.create(
                    index=index_name,
                    body={"mappings": mapping}
                )
            else:
                self.client.indices.create(index=index_name)
                
            logger.info(f"Created index {index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")
            return False
    
    def index_document(self, index_name: str, doc_id: str, document: Dict[str, Any]) -> bool:
        """Index a document in Elasticsearch"""
        self.ensure_initialized()
        
        try:
            self.client.index(
                index=index_name,
                id=doc_id,
                document=document
            )
            return True
        except Exception as e:
            logger.error(f"Failed to index document {doc_id} in {index_name}: {e}")
            return False
    
    def bulk_index(self, index_name: str, documents: List[Dict[str, Any]]) -> bool:
        """Bulk index multiple documents in Elasticsearch"""
        self.ensure_initialized()
        
        if not documents:
            return True
            
        try:
            # Prepare bulk operation
            bulk_data = []
            for doc in documents:
                # Extract ID from document
                doc_id = doc.pop('id', None)
                
                # Add index operation
                bulk_data.append({"index": {"_index": index_name, "_id": doc_id}})
                bulk_data.append(doc)
            
            # Execute bulk operation
            if bulk_data:
                self.client.bulk(body=bulk_data, refresh=True)
                logger.info(f"Bulk indexed {len(documents)} documents in {index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to bulk index documents in {index_name}: {e}")
            return False
    
    def delete_document(self, index_name: str, doc_id: str) -> bool:
        """Delete a document from Elasticsearch"""
        self.ensure_initialized()
        
        try:
            self.client.delete(index=index_name, id=doc_id)
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id} from {index_name}: {e}")
            return False
    
    def update_document(self, index_name: str, doc_id: str, document: Dict[str, Any]) -> bool:
        """Update a document in Elasticsearch"""
        self.ensure_initialized()
        
        try:
            self.client.update(
                index=index_name,
                id=doc_id,
                body={"doc": document}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update document {doc_id} in {index_name}: {e}")
            return False
    
    def search(self, index_name: str, query: Dict[str, Any], size: int = 10) -> Dict[str, Any]:
        """Search Elasticsearch index"""
        self.ensure_initialized()
        
        try:
            result = self.client.search(
                index=index_name,
                body=query,
                size=size
            )
            return result
        except Exception as e:
            logger.error(f"Search failed in {index_name}: {e}")
            return {"error": str(e)}
            
    def get_index_name(self, model_class: Type[Model]) -> str:
        """Generate index name for a model class"""
        app_label = model_class._meta.app_label
        model_name = model_class._meta.model_name
        return f"{ELASTICSEARCH_INDEX_PREFIX}_{app_label}_{model_name}".lower()


# Singleton instance
_elasticsearch_engine = None

def get_search_engine() -> ElasticsearchEngine:
    """Get the Elasticsearch engine instance"""
    global _elasticsearch_engine
    if _elasticsearch_engine is None:
        _elasticsearch_engine = ElasticsearchEngine()
    return _elasticsearch_engine


def prepare_document(obj: Model, fields: List[str], boost_fields: Dict[str, float] = None) -> Dict[str, Any]:
    """
    Prepare a document for indexing from a Django model instance.
    
    Args:
        obj: Django model instance
        fields: List of fields to include
        boost_fields: Dictionary of field names to boost values
        
    Returns:
        Dictionary representation of the object for indexing
    """
    document = {'id': obj.pk}
    
    for field in fields:
        value = getattr(obj, field, None)
        
        # Handle different field types
        if isinstance(value, (list, tuple)):
            # Convert lists to strings
            document[field] = ', '.join(str(v) for v in value)
        elif hasattr(value, 'isoformat'):
            # Convert dates/datetimes to ISO format
            document[field] = value.isoformat()
        else:
            # Use string representation for everything else
            document[field] = str(value) if value is not None else None
    
    return document

def index_objects(model_class: Type[Model], objects, fields: List[str], boost_fields: Dict[str, float] = None) -> bool:
    """
    Index multiple objects in the search engine.
    
    Args:
        model_class: Django model class
        objects: Queryset or list of objects to index
        fields: List of fields to include in the index
        boost_fields: Dictionary of field names to boost values
        
    Returns:
        True if indexing was successful, False otherwise
    """
    try:
        engine = get_search_engine()
        index_name = engine.get_index_name(model_class)
        
        # Create index if it doesn't exist
        # Create a basic mapping for text fields
        properties = {}
        for field in fields:
            field_obj = model_class._meta.get_field(field)
            field_type = field_obj.get_internal_type()
            
            if field_type in ('CharField', 'TextField'):
                properties[field] = {
                    "type": "text",
                    "analyzer": "standard",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256
                        }
                    }
                }
            elif field_type == 'DateTimeField':
                properties[field] = {"type": "date"}
            elif field_type == 'BooleanField':
                properties[field] = {"type": "boolean"}
            elif field_type in ('IntegerField', 'AutoField'):
                properties[field] = {"type": "integer"}
            elif field_type == 'FloatField':
                properties[field] = {"type": "float"}
            else:
                properties[field] = {"type": "keyword"}
        
        mapping = {"properties": properties}
        
        engine.create_index(index_name, mapping)
        
        # Prepare documents for indexing
        documents = [prepare_document(obj, fields, boost_fields) for obj in objects]
        
        # Index documents
        return engine.bulk_index(index_name, documents)
    
    except Exception as e:
        logger.error(f"Failed to index objects of {model_class.__name__}: {e}")
        return False


def update_object(model_class: Type[Model], obj: Model, fields: List[str]) -> bool:
    """
    Update an object in the search engine.
    
    Args:
        model_class: Django model class
        obj: Model instance to update
        fields: List of fields to include
        
    Returns:
        True if update was successful, False otherwise
    """
    try:
        engine = get_search_engine()
        index_name = engine.get_index_name(model_class)
        doc_id = str(obj.pk)
        
        # Prepare document
        document = prepare_document(obj, fields)
        
        # Update document
        return engine.update_document(index_name, doc_id, document)
    except Exception as e:
        logger.error(f"Failed to update object {obj.pk} in index: {e}")
        return False


def delete_object(model_class: Type[Model], obj_id: Union[str, int]) -> bool:
    """
    Delete an object from the search engine.
    
    Args:
        model_class: Django model class
        obj_id: ID of object to delete
        
    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        engine = get_search_engine()
        index_name = engine.get_index_name(model_class)
        
        # Delete document
        return engine.delete_document(index_name, str(obj_id))
    except Exception as e:
        logger.error(f"Failed to delete object {obj_id} from index: {e}")
        return False


def search_objects(model_class: Type[Model], query_text: str, fields: List[str] = None, 
                  filters: Dict[str, Any] = None, size: int = 10) -> List[Dict[str, Any]]:
    """
    Search for objects in the search engine.
    
    Args:
        model_class: Django model class to search
        query_text: Text to search for
        fields: Fields to search in (defaults to all indexed fields)
        filters: Additional filters to apply
        size: Maximum number of results
        
    Returns:
        List of search results
    """
    try:
        engine = get_search_engine()
        index_name = engine.get_index_name(model_class)
        
        # Determine fields to search
        if not fields:
            # Use all registered fields
            app_label = model_class._meta.app_label
            model_name = model_class._meta.model_name
            from services.search_service import _SEARCH_REGISTRY
            fields = _SEARCH_REGISTRY.get((app_label, model_name), {}).get('fields', [])
        
        # Build Elasticsearch query
        should_clauses = []
        
        # Add multi_match query
        should_clauses.append({
            "multi_match": {
                "query": query_text,
                "fields": fields,
                "fuzziness": "AUTO"
            }
        })
        
        query = {
            "query": {
                "bool": {
                    "should": should_clauses
                }
            }
        }
        
        # Add filters if provided
        if filters:
            filter_clauses = []
            for field, value in filters.items():
                filter_clauses.append({"term": {field: value}})
            
            query["query"]["bool"]["filter"] = filter_clauses
            
        # Add highlighting
        query["highlight"] = {
            "fields": {field: {} for field in fields},
            "pre_tags": ["<em>"],
            "post_tags": ["</em>"]
        }
        
        # Execute search
        result = engine.search(index_name, query, size)
        
        # Process results
        hits = result.get('hits', {}).get('hits', [])
        search_results = []
        
        for hit in hits:
            search_result = hit['_source']
            
            # Add highlight information if available
            if 'highlight' in hit:
                search_result['highlights'] = hit['highlight']
            
            # Add score
            search_result['_score'] = hit.get('_score')
            search_results.append(search_result)
            
        return search_results
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []
        
def generate_document_id() -> str:
    """Generate a unique ID for a document"""
    return str(uuid.uuid4())