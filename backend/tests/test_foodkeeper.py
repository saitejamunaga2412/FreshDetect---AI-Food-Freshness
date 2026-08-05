import os
import sys

sys.path.append(os.path.abspath("."))

from app.services.foodkeeper_service import FoodKeeperService

def test():
    fks = FoodKeeperService()
    foods = ['Apple', 'Banana', 'Bellpepper', 'Carrot', 'Cucumber', 'Grape', 'Guava', 'Jujube', 'Mango', 'Orange', 'Pomegranate', 'Potato', 'Strawberry', 'Tomato', 'Capsicum']
    
    for f in foods:
        res = fks.lookup(f)
        print(f"{f}: {'Found -> ' + res['name'] if res else 'Not Found'}")

if __name__ == "__main__":
    test()
