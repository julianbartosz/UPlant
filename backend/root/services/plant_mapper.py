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
    try:
        # Critical fields from top-level
        api_id = api_data.get("id")
        slug = api_data.get("slug")
        scientific_name = api_data.get("scientific_name")
        rank = api_data.get("rank")
        if api_id is None or slug is None or scientific_name is None or rank is None:
            raise MappingError("Missing one or more critical fields: id, slug, scientific_name, or rank.")
        
        # Direct mappings from top-level (with possibility of fallbacks)
        common_name = api_data.get("common_name")
        family_common_name = api_data.get("family_common_name")
        genus_id = api_data.get("genus_id")
        image_url = api_data.get("image_url")
        synonyms = api_data.get("synonyms", [])
        vegetable = api_data.get("vegetable", False)
        
        # Extract main_species from the API data to use as fallback if necessary.
        main_species = api_data.get("main_species", {})

        # Fallback mechanism for family and genus:
        family = extract_string(api_data.get("family"))
        if not family:
            family = extract_string(main_species.get("family"))
        genus = extract_string(api_data.get("genus"))
        if not genus:
            genus = extract_string(main_species.get("genus"))
        # Status and rank should preferably come from the detailed main_species.
        status = main_species.get("status") or api_data.get("status")
        rank = main_species.get("rank") or rank

        # Use fallback values for common_name, family_common_name, synonyms, and vegetable.
        common_name = common_name or main_species.get("common_name")
        family_common_name = family_common_name or main_species.get("family_common_name")
        synonyms = main_species.get("synonyms") if main_species.get("synonyms") is not None else synonyms
        if vegetable is None:
            vegetable = main_species.get("vegetable", False)

        # Additional fields from main_species for detailed mapping
        duration = main_species.get("duration")
        edible = main_species.get("edible")
        edible_part = main_species.get("edible_part")

        # For growth values, extract from main_species.growth if available.
        growth = main_species.get("growth", {})
        days_to_harvest = growth.get("days_to_harvest")
        sowing = growth.get("sowing")
        # row_spacing and spread are nested objects; for example:
        row_spacing_cm = None
        if "row_spacing" in growth and isinstance(growth["row_spacing"], dict):
            row_spacing_cm = growth["row_spacing"].get("cm")
        spread_cm = None
        if "spread" in growth and isinstance(growth["spread"], dict):
            spread_cm = growth["spread"].get("cm")
        ph_minimum = growth.get("ph_minimum")
        ph_maximum = growth.get("ph_maximum")
        light = growth.get("light")
        atmospheric_humidity = growth.get("atmospheric_humidity")
        min_temperature = growth.get("minimum_temperature", {}).get("deg_c")
        max_temperature = growth.get("maximum_temperature", {}).get("deg_c")
        minimum_precipitation = None
        if "minimum_precipitation" in growth and isinstance(growth["minimum_precipitation"], dict):
            minimum_precipitation = growth["minimum_precipitation"].get("mm")
        maximum_precipitation = None
        if "maximum_precipitation" in growth and isinstance(growth["maximum_precipitation"], dict):
            maximum_precipitation = growth["maximum_precipitation"].get("mm")
        minimum_root_depth = None
        if "minimum_root_depth" in growth and isinstance(growth["minimum_root_depth"], dict):
            minimum_root_depth = growth["minimum_root_depth"].get("cm")
        growth_months = growth.get("growth_months")
        bloom_months = growth.get("bloom_months")
        fruit_months = growth.get("fruit_months")

        # Extract details for flower, foliage, fruit, and specifications from main_species:
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
        average_height = None
        if "average_height" in specifications and isinstance(specifications["average_height"], dict):
            average_height = specifications["average_height"].get("cm")
        maximum_height = None
        if "maximum_height" in specifications and isinstance(specifications["maximum_height"], dict):
            maximum_height = specifications["maximum_height"].get("cm")
        toxicity = specifications.get("toxicity")
        
        plant_data = {
            "api_id": api_id,
            "common_name": common_name,
            "slug": slug,
            "scientific_name": scientific_name,
            "status": status,
            "rank": rank,
            "family_common_name": family_common_name,
            "family": family,
            "genus_id": genus_id,
            "genus": genus,
            "image_url": image_url,
            "synonyms": synonyms,
            "vegetable": vegetable,
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
            "min_temperature": min_temperature,
            "max_temperature": max_temperature,
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
