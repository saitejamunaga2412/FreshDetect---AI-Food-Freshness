import os
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class FoodKeeperService:
    _instance = None
    _dataset = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FoodKeeperService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Prevent re-initialization
        if self._dataset is not None:
            return

        csv_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "dataset",
            "processed",
            "foodkeeper_fruits_vegetables.csv"
        )
        
        try:
            self._dataset = pd.read_csv(os.path.abspath(csv_path))
            # Convert 'Name' to lowercase for case-insensitive lookup
            self._dataset['name_lower'] = self._dataset['Name'].str.lower()
            logger.info("FoodKeeper dataset loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load FoodKeeper dataset: {e}")
            self._dataset = pd.DataFrame()

    def lookup(self, fruit_name: str):
        """
        Search for fruit in FoodKeeper dataset (case-insensitive).
        Returns None if not found.
        """
        if self._dataset is None or self._dataset.empty:
            return None
            
        if not fruit_name:
            return None

        # 1. Normalize names
        normalization_map = {
            "carrot": "carrots, parsnips",
            "potato": "potatoes",
            "tomato": "tomatoes",
            "bellpepper": "peppers",
            "orange": "citrus fruit",
            "apple": "apples",
            "banana": "bananas",
            "grape": "grapes",
            "strawberry": "strawberries",
            "mango": "papaya, mango, feijoa, passionfruit, casaha melon",
            "cucumber": "cucumbers",
            "pomegranate": "pomegranate",
            "capsicum": "peppers",
            "brinjal": "eggplant"
        }
        
        search_term = fruit_name.lower()
        normalized_term = normalization_map.get(search_term, search_term)
        
        # 2. Case-insensitive exact match
        match = self._dataset[self._dataset['name_lower'] == normalized_term]
        
        confidence = 1.0
        
        # 3. Fuzzy search if no exact match exists
        if match.empty:
            import difflib
            all_names = self._dataset['name_lower'].dropna().tolist()
            # 4. If multiple matches exist, select the highest similarity
            matches = difflib.get_close_matches(normalized_term, all_names, n=1, cutoff=0.7)
            
            if matches:
                best_match_str = matches[0]
                confidence = difflib.SequenceMatcher(None, normalized_term, best_match_str).ratio()
                match = self._dataset[self._dataset['name_lower'] == best_match_str]
        
        if match.empty:
            logger.info(f"FoodKeeper lookup: Requested '{fruit_name}' -> No match found.")
            return None

        record = match.iloc[0]
        matched_name = record.get("Name", "")
        
        # 5. Log the requested name, matched entry, and confidence
        logger.info(f"FoodKeeper lookup: Requested '{fruit_name}' -> Matched '{matched_name}' with confidence {confidence:.2f}")
        
        # Extract Shelf Life Dict dynamically
        shelf_life = {}
        if pd.notna(record.get('Pantry_Max')) and pd.notna(record.get('Pantry_Metric')):
            shelf_life["pantry"] = f"{int(record.get('Pantry_Max')) if float(record.get('Pantry_Max')).is_integer() else record.get('Pantry_Max')} {record.get('Pantry_Metric')}".strip()
        if pd.notna(record.get('Refrigerate_Max')) and pd.notna(record.get('Refrigerate_Metric')):
            shelf_life["refrigerator"] = f"{int(record.get('Refrigerate_Max')) if float(record.get('Refrigerate_Max')).is_integer() else record.get('Refrigerate_Max')} {record.get('Refrigerate_Metric')}".strip()
        if pd.notna(record.get('Freeze_Max')) and pd.notna(record.get('Freeze_Metric')):
            shelf_life["freezer"] = f"{int(record.get('Freeze_Max')) if float(record.get('Freeze_Max')).is_integer() else record.get('Freeze_Max')} {record.get('Freeze_Metric')}".strip()
        
        # Determine best storage area natively from the dataset columns (Prioritize Refrigerator -> Pantry -> Freezer)
        storage_area = "Not Available"
        if "refrigerator" in shelf_life:
            storage_area = "Refrigerator"
        elif "pantry" in shelf_life:
            storage_area = "Pantry"
        elif "freezer" in shelf_life:
            storage_area = "Freezer"
            
        # Extract Storage Instructions dynamically
        tips = []
        if pd.notna(record.get('Refrigerate_tips')):
            tips.append(str(record.get('Refrigerate_tips')))
        if pd.notna(record.get('Pantry_tips')) and str(record.get('Pantry_tips')) not in tips:
            tips.append(str(record.get('Pantry_tips')))
        if pd.notna(record.get('Freeze_Tips')) and str(record.get('Freeze_Tips')) not in tips:
            tips.append(str(record.get('Freeze_Tips')))
            
        storage_tips = " ".join(tips).strip()
            
        return {
            "name": str(record.get("Name", "")),
            "recommended_temperature": "Not Available in Dataset",
            "recommended_humidity": "Not Available in Dataset",
            "packaging_material": "Not Available in Dataset",
            "storage_area": storage_area,
            "shelf_life": shelf_life,
            "storage_instructions": storage_tips if storage_tips else "Not Available"
        }

    @staticmethod
    def parse_shelf_life_string(shelf_life_str: str) -> int:
        """Parses 'X Days', 'X Weeks', 'X Months' into total days. Returns None if invalid."""
        if not shelf_life_str: return None
        parts = str(shelf_life_str).split()
        if len(parts) < 2: return None
        
        try:
            val = float(parts[0])
            unit = parts[1].lower()
            if "day" in unit: return int(val)
            if "week" in unit: return int(val * 7)
            if "month" in unit: return int(val * 30.44)
            if "year" in unit: return int(val * 365)
        except:
            return None
        return None
