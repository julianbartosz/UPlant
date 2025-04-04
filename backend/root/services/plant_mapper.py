# backend/root/services/plant_mapper.py

from plants.models import Plant

class MappingError(Exception):
    """Custom exception raised when API data cannot be mapped to a Plant."""
    pass

def extract_string(value):
    """If the input is a dict, return its 'name' key; otherwise return the value as is."""
    if isinstance(value, dict):
        return value.get("name")
    return value

def map_api_to_plant(api_data: dict) -> dict:
    """
    Map processed API data to a dictionary suitable for creating/updating a Django Plant instance.
    
    Basic fields (from top-level):
      - id → api_id
      - common_name, slug, scientific_name, rank,
        family_common_name, genus_id, image_url, synonyms, vegetable
      
    For 'family' and 'genus', use a fallback:
      1. Check top-level fields.
      2. If missing or if the value is a dict, check in the 'main_species' object.

    Additionally, map extra fields from the nested 'main_species' object:
      - duration, edible, edible_part
      - Growth: days_to_harvest, sowing, row_spacing_cm, spread_cm, ph_minimum, ph_maximum,
                light, atmospheric_humidity, minimum_precipitation, maximum_precipitation,
                minimum_root_depth, growth_months, bloom_months, fruit_months
      - Flower: flower_color, flower_conspicuous
      - Foliage: foliage_texture, foliage_color, foliage_retention
      - Fruit/Seed: fruit_or_seed_conspicuous, fruit_or_seed_color, fruit_or_seed_shape, fruit_or_seed_persistence
      - Specifications: growth_rate, average_height, maximum_height, toxicity

    Raises:
      MappingError: If any critical field (id, slug, scientific_name, rank, or family/genus) is missing.
    """
    try:
        # Critical fields from top-level
        api_id = api_data.get("id")
        slug = api_data.get("slug")
        scientific_name = api_data.get("scientific_name")
        rank = api_data.get("rank")
        if api_id is None or slug is None or scientific_name is None or rank is None:
            raise MappingError("Missing one or more critical fields: id, slug, scientific_name, or rank.")
        
        # Direct mappings
        common_name = api_data.get("common_name")
        family_common_name = api_data.get("family_common_name")
        genus_id = api_data.get("genus_id")
        image_url = api_data.get("image_url")
        synonyms = api_data.get("synonyms", [])
        vegetable = api_data.get("vegetable", False)
        
        # Fallback mechanism for family and genus:
        family = extract_string(api_data.get("family"))
        genus = extract_string(api_data.get("genus"))
        status = api_data.get("status")
        main_species = api_data.get("main_species", {})
        if not family:
            family = extract_string(main_species.get("family"))
        if not genus:
            genus = extract_string(main_species.get("genus"))
        if not status:
            status = main_species.get("status")
        # Make sure status is not null
        if not api_data.get("status"):
            api_data["status"] = "unknown"
        if not family or not genus:
            raise MappingError("Missing 'family', 'genus', or 'status' in both top-level and nested 'main_species' data.")
        
        # Additional fields from main_species
        duration = main_species.get("duration")
        edible = main_species.get("edible")
        if edible is None:
            edible = False
        edible_part = main_species.get("edible_part")
        
        growth = main_species.get("growth", {})
        days_to_harvest = growth.get("days_to_harvest")
        sowing = growth.get("sowing")
        row_spacing_cm = growth.get("row_spacing", {}).get("cm")
        spread_cm = growth.get("spread", {}).get("cm")
        ph_minimum = growth.get("ph_minimum")
        ph_maximum = growth.get("ph_maximum")
        light = growth.get("light")
        atmospheric_humidity = growth.get("atmospheric_humidity")
        minimum_precipitation = growth.get("minimum_precipitation", {}).get("mm")
        maximum_precipitation = growth.get("maximum_precipitation", {}).get("mm")
        minimum_root_depth = growth.get("minimum_root_depth", {}).get("cm")
        growth_months = growth.get("growth_months")
        bloom_months = growth.get("bloom_months")
        fruit_months = growth.get("fruit_months")
        
        flower = main_species.get("flower", {})
        flower_color = flower.get("color")
        flower_conspicuous = flower.get("conspicuous")
        
        foliage = main_species.get("foliage", {})
        foliage_texture = foliage.get("texture")
        foliage_color = foliage.get("color")
        foliage_retention = foliage.get("leaf_retention")
        
        fruit_or_seed = main_species.get("fruit_or_seed", {})
        fruit_or_seed_conspicuous = fruit_or_seed.get("conspicuous")
        fruit_or_seed_color = fruit_or_seed.get("color")
        fruit_or_seed_shape = fruit_or_seed.get("shape")
        fruit_or_seed_persistence = fruit_or_seed.get("seed_persistence")
        
        specifications = main_species.get("specifications", {})
        growth_rate = specifications.get("growth_rate")
        average_height = specifications.get("average_height", {}).get("cm")
        maximum_height = specifications.get("maximum_height", {}).get("cm")
        toxicity = specifications.get("toxicity")
        
        plant_data = {
            "api_id": api_id,
            "common_name": common_name,
            "slug": slug,
            "scientific_name": scientific_name,
            "rank": rank,
            "status": status,
            "family_common_name": family_common_name,
            "family": family,
            "genus_id": genus_id,
            "genus": genus,
            "image_url": image_url,
            "synonyms": synonyms,
            "vegetable": vegetable,
            # Additional fields from main_species
            "duration": duration,
            "edible": edible,
            "edible_part": edible_part,
            "days_to_harvest": days_to_harvest,
            "sowing": sowing,
            "row_spacing_cm": row_spacing_cm,
            "spread_cm": spread_cm,
            "ph_minimum": ph_minimum,
            "ph_maximum": ph_maximum,
            "light": light,
            "atmospheric_humidity": atmospheric_humidity,
            "minimum_precipitation": minimum_precipitation,
            "maximum_precipitation": maximum_precipitation,
            "minimum_root_depth": minimum_root_depth,
            "growth_months": growth_months,
            "bloom_months": bloom_months,
            "fruit_months": fruit_months,
            "flower_color": flower_color,
            "flower_conspicuous": flower_conspicuous,
            "foliage_texture": foliage_texture,
            "foliage_color": foliage_color,
            "foliage_retention": foliage_retention,
            "fruit_or_seed_conspicuous": fruit_or_seed_conspicuous,
            "fruit_or_seed_color": fruit_or_seed_color,
            "fruit_or_seed_shape": fruit_or_seed_shape,
            "fruit_or_seed_persistence": fruit_or_seed_persistence,
            "growth_rate": growth_rate,
            "average_height": average_height,
            "maximum_height": maximum_height,
            "toxicity": toxicity,
        }
        return plant_data

    except Exception as e:
        raise MappingError(f"Error mapping API data: {str(e)}") from e
