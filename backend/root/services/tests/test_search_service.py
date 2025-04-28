import pytest
import logging
from unittest.mock import patch, MagicMock, call
from django.db.models import Q
from django.core.cache import cache
from django.db import models
from django.conf import settings

from services.search_service import (
    register_search_models,
    perform_search,
    clean_query,
    _generate_cache_key,
    reindex_model,
    get_search_suggestions,
    _SEARCH_REGISTRY
)

# Test model classes
class TestPlant(models.Model):
    common_name = models.CharField(max_length=100)
    scientific_name = models.CharField(max_length=100)
    description = models.TextField()
    care_instructions = models.TextField()
    water_interval = models.IntegerField(default=7)

    class Meta:
        app_label = 'test_app'


class TestGarden(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    location = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'test_app'


@pytest.fixture
def clear_registry():
    """Clear the search registry before and after tests."""
    _SEARCH_REGISTRY.clear()
    yield
    _SEARCH_REGISTRY.clear()


@pytest.fixture
def mock_test_models():
    """Set up mock models for testing."""
    with patch.object(TestPlant._meta, 'app_label', 'test_app'), \
         patch.object(TestPlant._meta, 'model_name', 'testplant'), \
         patch.object(TestGarden._meta, 'app_label', 'test_app'), \
         patch.object(TestGarden._meta, 'model_name', 'testgarden'):
        yield


@pytest.fixture
def mock_queryset():
    """Create a mock queryset for testing."""
    mock_qs = MagicMock()
    mock_qs.filter.return_value = mock_qs
    mock_qs.order_by.return_value = mock_qs
    return mock_qs


@pytest.fixture
def mock_plants():
    """Create mock plant objects for testing."""
    plants = [
        MagicMock(
            id=1,
            common_name='Tomato',
            scientific_name='Solanum lycopersicum',
            description='A red fruit/vegetable',
        ),
        MagicMock(
            id=2, 
            common_name='Basil',
            scientific_name='Ocimum basilicum',
            description='A fragrant herb',
        ),
        MagicMock(
            id=3,
            common_name='Rosemary',
            scientific_name='Salvia rosmarinus',
            description='An aromatic herb',
        )
    ]
    return plants


@pytest.fixture
def mock_gardens():
    """Create mock garden objects for testing."""
    gardens = [
        MagicMock(
            id=1,
            name='Vegetable Garden',
            description='For growing vegetables',
            location='Backyard',
        ),
        MagicMock(
            id=2,
            name='Herb Garden',
            description='For growing herbs',
            location='Kitchen window',
        )
    ]
    return gardens


class TestRegisterSearchModels:
    """Tests for register_search_models function."""

    def test_basic_registration(self, clear_registry, mock_test_models):
        """Test basic model registration."""
        result = register_search_models(TestPlant)
        
        assert result is True
        assert ('test_app', 'testplant') in _SEARCH_REGISTRY
        assert _SEARCH_REGISTRY[('test_app', 'testplant')]['model'] == TestPlant
        
        # Check default fields (look for CharFields and TextFields)
        assert 'common_name' in _SEARCH_REGISTRY[('test_app', 'testplant')]['fields']
        assert 'scientific_name' in _SEARCH_REGISTRY[('test_app', 'testplant')]['fields']
        assert 'description' in _SEARCH_REGISTRY[('test_app', 'testplant')]['fields']
        assert 'care_instructions' in _SEARCH_REGISTRY[('test_app', 'testplant')]['fields']
        
        # Check water_interval is excluded (it's an IntegerField)
        assert 'water_interval' not in _SEARCH_REGISTRY[('test_app', 'testplant')]['fields']

    def test_registration_with_explicit_fields(self, clear_registry, mock_test_models):
        """Test registration with explicitly provided fields."""
        fields = ['common_name', 'scientific_name']
        result = register_search_models(TestPlant, fields=fields)
        
        assert result is True
        assert ('test_app', 'testplant') in _SEARCH_REGISTRY
        assert _SEARCH_REGISTRY[('test_app', 'testplant')]['fields'] == fields
        
        # Check other fields are excluded
        assert 'description' not in _SEARCH_REGISTRY[('test_app', 'testplant')]['fields']

    def test_registration_with_boost_fields(self, clear_registry, mock_test_models):
        """Test registration with boost fields."""
        boost_fields = {'common_name': 2.0, 'scientific_name': 1.5}
        result = register_search_models(TestPlant, boost_fields=boost_fields)
        
        assert result is True
        assert _SEARCH_REGISTRY[('test_app', 'testplant')]['boost_fields'] == boost_fields

    def test_registration_with_exclude_fields(self, clear_registry, mock_test_models):
        """Test registration with excluded fields."""
        exclude_fields = ['description']
        result = register_search_models(TestPlant, exclude_fields=exclude_fields)
        
        assert result is True
        assert 'common_name' in _SEARCH_REGISTRY[('test_app', 'testplant')]['fields']
        assert 'scientific_name' in _SEARCH_REGISTRY[('test_app', 'testplant')]['fields']
        assert 'description' not in _SEARCH_REGISTRY[('test_app', 'testplant')]['fields']

    def test_multiple_registrations(self, clear_registry, mock_test_models):
        """Test registering multiple models."""
        register_search_models(TestPlant)
        register_search_models(TestGarden)
        
        assert ('test_app', 'testplant') in _SEARCH_REGISTRY
        assert ('test_app', 'testgarden') in _SEARCH_REGISTRY
        assert len(_SEARCH_REGISTRY) == 2


class TestPerformSearch:
    """Tests for perform_search function."""

    def test_empty_query(self, clear_registry):
        """Test searching with an empty query."""
        results = perform_search("")
        assert results == []

    def test_clean_query_called(self, clear_registry, mock_test_models):
        """Test that clean_query is called on the query text."""
        with patch('services.search_service.clean_query') as mock_clean:
            mock_clean.return_value = "cleaned query"
            with patch('services.search_service._SEARCH_REGISTRY', {}):
                perform_search("raw query")
            mock_clean.assert_called_once_with("raw query")

    @patch('django.core.cache.cache.get')
    def test_cache_hit(self, mock_cache_get, clear_registry, mock_test_models):
        """Test that cached results are returned when available."""
        cached_results = ['cached_result1', 'cached_result2']
        mock_cache_get.return_value = cached_results
        
        results = perform_search("test query", TestPlant)
        
        assert results == cached_results
        mock_cache_get.assert_called_once()

    @patch('django.core.cache.cache.get', return_value=None)
    @patch('django.core.cache.cache.set')
    def test_search_single_model(self, mock_cache_set, mock_cache_get, clear_registry, mock_test_models, mock_plants):
        """Test searching a single model."""
        # Register the test model
        register_search_models(TestPlant)
        
        # Setup mock queryset and objects
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.__getitem__.return_value = mock_plants
        
        with patch.object(TestPlant.objects, 'all', return_value=mock_qs):
            results = perform_search("tomato", TestPlant)
            
            # Check that the filter was called with the right arguments
            mock_qs.filter.assert_called()
            
            # Check that results are returned
            assert results == mock_plants
            
            # Check that results are cached
            mock_cache_set.assert_called_once()

    @patch('django.core.cache.cache.get', return_value=None)
    def test_search_all_models(self, mock_cache_get, clear_registry, mock_test_models, mock_plants, mock_gardens):
        """Test searching across all registered models."""
        # Register multiple test models
        register_search_models(TestPlant)
        register_search_models(TestGarden)
        
        # Setup mock querysets and objects
        plant_qs = MagicMock()
        plant_qs.filter.return_value = plant_qs
        plant_qs.__getitem__.return_value = mock_plants
        
        garden_qs = MagicMock()
        garden_qs.filter.return_value = garden_qs
        garden_qs.__getitem__.return_value = mock_gardens
        
        with patch.object(TestPlant.objects, 'all', return_value=plant_qs), \
             patch.object(TestGarden.objects, 'all', return_value=garden_qs):
            results = perform_search("garden")
            
            # Check that both querysets were filtered
            plant_qs.filter.assert_called_once()
            garden_qs.filter.assert_called_once()
            
            # Results should include both plants and gardens
            assert len(results) > 0  # Can't assert exact results as they depend on mock __getitem__

    @patch('django.core.cache.cache.get', return_value=None)
    def test_search_with_additional_filters(self, mock_cache_get, clear_registry, mock_test_models, mock_plants):
        """Test searching with additional filters."""
        register_search_models(TestPlant)
        
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.__getitem__.return_value = mock_plants
        
        with patch.object(TestPlant.objects, 'all', return_value=mock_qs):
            additional_filters = {'edible': True}
            perform_search("tomato", TestPlant, additional_filters=additional_filters)
            
            # Check that the additional filter was applied
            assert mock_qs.filter.call_count == 2  # Once for search query, once for additional filters

    @patch('django.core.cache.cache.get', return_value=None)
    def test_search_with_order_by(self, mock_cache_get, clear_registry, mock_test_models, mock_plants):
        """Test searching with order_by parameter."""
        register_search_models(TestPlant)
        
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.__getitem__.return_value = mock_plants
        
        with patch.object(TestPlant.objects, 'all', return_value=mock_qs):
            perform_search("tomato", TestPlant, order_by="common_name")
            
            # Check that order_by was applied
            mock_qs.order_by.assert_called_once_with("common_name")

    @patch('django.core.cache.cache.get', return_value=None)
    def test_search_with_limit(self, mock_cache_get, clear_registry, mock_test_models):
        """Test that limit parameter is respected."""
        register_search_models(TestPlant)
        
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        
        with patch.object(TestPlant.objects, 'all', return_value=mock_qs):
            perform_search("tomato", TestPlant, limit=5)
            
            # Check that limit is applied via slicing
            mock_qs.__getitem__.assert_called_with(slice(None, 5))

    @patch('django.core.cache.cache.get', return_value=None)
    def test_unregistered_model_fallback(self, mock_cache_get, clear_registry, mock_test_models):
        """Test fallback behavior when searching unregistered model."""
        # Don't register the model
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        
        with patch.object(TestPlant.objects, 'all', return_value=mock_qs):
            perform_search("tomato", TestPlant)
            
            # Check that a default set of fields was used
            mock_qs.filter.assert_called()

    @patch('django.core.cache.cache.get', side_effect=Exception("Cache error"))
    @patch('services.search_service.logger')
    def test_cache_error_handling(self, mock_logger, mock_cache_get, clear_registry, mock_test_models):
        """Test error handling when cache operations fail."""
        register_search_models(TestPlant)
        
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.__getitem__.return_value = []
        
        with patch.object(TestPlant.objects, 'all', return_value=mock_qs):
            results = perform_search("tomato", TestPlant)
            
            # Search should continue despite cache error
            assert mock_logger.error.called
            assert isinstance(results, list)


class TestCleanQuery:
    """Tests for clean_query function."""

    def test_special_character_removal(self):
        """Test removing special characters from query."""
        query = "tomato!@#$%"
        cleaned = clean_query(query)
        assert cleaned == "tomato"

    def test_whitespace_normalization(self):
        """Test normalizing whitespace in query."""
        query = "  tomato    plant  "
        cleaned = clean_query(query)
        assert cleaned == "tomato plant"

    def test_lowercase_conversion(self):
        """Test converting query to lowercase."""
        query = "ToMaTo PlAnT"
        cleaned = clean_query(query)
        assert cleaned == "tomato plant"

    def test_combined_cleaning(self):
        """Test all cleaning operations together."""
        query = "  ToMaTo!   PlAnT@#$  "
        cleaned = clean_query(query)
        assert cleaned == "tomato plant"


class TestGenerateCacheKey:
    """Tests for _generate_cache_key function."""

    def test_basic_key_generation(self):
        """Test generating a basic cache key."""
        key = _generate_cache_key("tomato", "TestPlant", None, None)
        assert key == "search:TestPlant:tomato"

    def test_key_with_additional_filters(self):
        """Test cache key with additional filters."""
        additional_filters = {'edible': True, 'vegetable': True}
        key = _generate_cache_key("tomato", "TestPlant", additional_filters, None)
        # Filters should be sorted alphabetically for consistency
        assert "edible:True" in key
        assert "vegetable:True" in key

    def test_key_with_order_by(self):
        """Test cache key with order_by parameter."""
        key = _generate_cache_key("tomato", "TestPlant", None, "common_name")
        assert key.endswith("order:common_name")

    def test_complex_key_generation(self):
        """Test generating a key with all parameters."""
        additional_filters = {'edible': True}
        key = _generate_cache_key("tomato", "TestPlant", additional_filters, "common_name")
        assert "search:TestPlant:tomato" in key
        assert "edible:True" in key
        assert "order:common_name" in key


@pytest.mark.parametrize('enable_advanced_search', [True, False])
class TestReindexModel:
    """Tests for reindex_model function."""

    def test_reindex_all_instances(self, enable_advanced_search, clear_registry, mock_test_models):
        """Test reindexing all instances of a model."""
        register_search_models(TestPlant)
        
        with patch('services.search_service.ENABLE_ADVANCED_SEARCH', enable_advanced_search):
            if enable_advanced_search:
                with patch('services.search_service.index_objects') as mock_index:
                    reindex_model(TestPlant)
                    mock_index.assert_called_once()
            else:
                with patch('django.core.cache.cache.keys') as mock_keys, \
                     patch('django.core.cache.cache.delete_many') as mock_delete_many:
                    mock_keys.return_value = ['search:TestPlant:tomato', 'search:TestPlant:basil']
                    reindex_model(TestPlant)
                    mock_delete_many.assert_called_once_with(['search:TestPlant:tomato', 'search:TestPlant:basil'])

    def test_reindex_specific_instances(self, enable_advanced_search, clear_registry, mock_test_models):
        """Test reindexing specific instances of a model."""
        register_search_models(TestPlant)
        instance_ids = [1, 2, 3]
        
        with patch('services.search_service.ENABLE_ADVANCED_SEARCH', enable_advanced_search):
            if enable_advanced_search:
                with patch('services.search_service.index_objects') as mock_index, \
                     patch.object(TestPlant.objects, 'filter') as mock_filter:
                    reindex_model(TestPlant, instance_ids)
                    mock_filter.assert_called_once_with(id__in=instance_ids)
                    mock_index.assert_called_once()
            else:
                with patch('django.core.cache.cache.keys') as mock_keys, \
                     patch('django.core.cache.cache.delete_many') as mock_delete_many:
                    mock_keys.return_value = ['search:TestPlant:tomato']
                    reindex_model(TestPlant, instance_ids)
                    mock_delete_many.assert_called_once()

    def test_unregistered_model(self, enable_advanced_search, clear_registry, mock_test_models):
        """Test reindexing an unregistered model."""
        # Don't register the model
        result = reindex_model(TestPlant)
        assert result is False

    def test_cache_keys_error_handling(self, enable_advanced_search, clear_registry, mock_test_models):
        """Test error handling when cache.keys() is not supported."""
        register_search_models(TestPlant)
        
        with patch('services.search_service.ENABLE_ADVANCED_SEARCH', False):
            with patch('django.core.cache.cache.keys', side_effect=AttributeError("keys() not supported")), \
                 patch('django.core.cache.cache.delete') as mock_delete:
                reindex_model(TestPlant)
                # Should fall back to deleting specific keys
                assert mock_delete.call_count >= 3


class TestGetSearchSuggestions:
    """Tests for get_search_suggestions function."""

    def test_short_prefix(self, clear_registry):
        """Test with prefix shorter than 2 characters."""
        suggestions = get_search_suggestions("a")
        assert suggestions == []

    def test_clean_prefix(self, clear_registry):
        """Test that prefix is cleaned."""
        with patch('services.search_service.clean_query') as mock_clean:
            mock_clean.return_value = "tomato"
            get_search_suggestions("tomato!")
            mock_clean.assert_called_once_with("tomato!")

    def test_specific_model_suggestions(self, clear_registry, mock_test_models):
        """Test getting suggestions from a specific model."""
        register_search_models(TestPlant)
        
        mock_qs = MagicMock()
        mock_values = MagicMock()
        mock_distinct = MagicMock()
        mock_qs.filter.return_value = mock_values
        mock_values.values_list.return_value = mock_distinct
        mock_distinct.distinct.return_value = ["Tomato", "Tomato Plant"]
        
        with patch.object(TestPlant.objects, 'filter', return_value=mock_values):
            suggestions = get_search_suggestions("tom", TestPlant)
            
            # Check that filter was called with istartswith
            TestPlant.objects.filter.assert_called_with(common_name__istartswith="tom")
            
            # Check that values_list and distinct were called
            mock_values.values_list.assert_called_with("common_name", flat=True)
            
            # Check that results are returned
            assert suggestions == ["Tomato", "Tomato Plant"]

    def test_first_available_model(self, clear_registry, mock_test_models):
        """Test getting suggestions from first available model if none specified."""
        register_search_models(TestPlant)
        register_search_models(TestGarden)
        
        mock_qs = MagicMock()
        mock_values = MagicMock()
        mock_distinct = MagicMock()
        mock_qs.filter.return_value = mock_values
        mock_values.values_list.return_value = mock_distinct
        mock_distinct.distinct.return_value = ["Tomato", "Tomato Plant"]
        
        with patch.object(TestPlant.objects, 'filter', return_value=mock_values):
            suggestions = get_search_suggestions("tom")
            
            # Should use first registered model that has the field
            TestPlant.objects.filter.assert_called_once()
            assert suggestions == ["Tomato", "Tomato Plant"]

    def test_limit_enforced(self, clear_registry, mock_test_models):
        """Test that limit parameter is respected."""
        register_search_models(TestPlant)
        
        mock_qs = MagicMock()
        mock_values = MagicMock()
        mock_distinct = MagicMock()
        mock_qs.filter.return_value = mock_values
        mock_values.values_list.return_value = mock_distinct
        mock_distinct.distinct.return_value = ["A", "B", "C", "D", "E"]
        
        with patch.object(TestPlant.objects, 'filter', return_value=mock_values):
            suggestions = get_search_suggestions("test", TestPlant, limit=3)
            
            # Check that slicing is applied to limit the results
            mock_distinct.distinct.return_value.__getitem__.assert_called_with(slice(None, 3))