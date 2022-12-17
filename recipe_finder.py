import requests
import time
import json
import random
import os
import io
import logging
import sys
import re
from collections import Counter


BASE_URL = "https://www.thecocktaildb.com/api/json/v1/1/search.php?s="
BASE_LIQUORS = ["vodka", "whiskey", "rum", "tequila", "brandy", "gin"]
CURR_DIR, BASE_FILENAME, FILE_SUFFIX = os.getcwd(), "drinks_data", ".json"
PATH = os.path.join(CURR_DIR, BASE_FILENAME + FILE_SUFFIX)
WORD_SET = set()

logging.basicConfig(stream=sys.stdout, level=logging.ERROR)


class TrieNode:
    """A class that represents a node for Trie data structure."""

    def __init__(self):
        self.children = {}
        self.recipe = ""


class Trie:
    """A class for Trie data structure composed of ingredients."""

    def __init__(self):
        self.root = TrieNode()

    def populate_recipes(self, recipe: str, ingredients: list[str]):
        """Maps recipe with its ingredients.
        It also marks the recipe name on the last ingredient.
        """
        node = self.root
        for ingredient in ingredients:
            if ingredient not in node.children:
                node.children[ingredient] = TrieNode()
            node = node.children[ingredient]
        node.recipe = recipe

    def search(self, ingredients: list, result: set):
        """Iterates over the ingredients and traverses the Trie."""
        node = self.root
        for i, ingredient in enumerate(ingredients):
            if ingredient in node.children:
                node = node.children[ingredient]
                if node.recipe and node.recipe not in result:
                    result.add(node.recipe)
            self.search(ingredients[i + 1 :], result)


def get_recipe_ingredients(base_liquors: list[str]):
    """Loads drinks data and extracts the ingredients for every recipe."""
    result = {}
    load_drink_data(base_liquors)

    with open(PATH) as file:
        json_file = json.load(file)

    for base_liquor in base_liquors:
        drink_dict = {}
        for drink in json_file[base_liquor]:
            drink_name = drink.get("strDrink")
            ingr_list = get_ingredient(drink)
            drink_dict[drink_name] = ingr_list
        result.update(drink_dict)
    return result


def load_drink_data(base_liquors: list[str]) -> None:
    """Checks if drinks data file exists or create data file via the api."""
    if os.path.isfile(PATH) and os.access(PATH, os.R_OK):
        logging.info("Drink data file already exists")
    else:
        logging.info("Either file is missing or is not readable, generating file...")
        raw_data = {}
        for base_liquor in base_liquors:
            raw_data[base_liquor] = get_liquor_recipes(base_liquor, 1)
        with io.open(PATH, "w") as outfile:
            json.dump(raw_data, outfile)


def get_liquor_recipes(liquor_type: str, retry: int) -> str:
    """Fetches a list of drinks data per liquor type."""
    headers = {"Accept": "application/json"}
    url = BASE_URL + liquor_type
    try:
        r = requests.get(url, headers=headers).json()
    except (requests.exceptions.HTTPError, json.decoder.JSONDecodeError):
        logging.error("Either file is missing or is not readable, generating file...")
        time.sleep(2**retry + random.uniform(0, 1))  # exponential backoff
        return get_liquor_recipes(liquor_type, retry + 1)
    else:
        return r.get("drinks")


def groupify(item: str):
    """Generalizes ingredients."""
    if "rum" in item:
        return "rum"
    if "whiskey" in item:
        return "whiskey"
    if "brandy" in item:
        return "brandy"
    if "gin" in item and not "ginger" in item:
        return "gin"
    if "bitters" in item:
        return "bitters"
    if "cherry" in item:
        return "cherry"
    if "peel" in item:
        if "lime" in item:
            return "lime"
        if "lemon" in item:
            return "lemon"
        if "orange" in item:
            return "orange"
    if "powdered" in item and "sugar" in item:
        return "sugar"
    if "egg" in item and "white" in item:
        return "egg"
    if "soda" in item:
        return "soda"
    if "cream" in item:
        return "cream"
    if "syrup" in item:
        return "syrup"
    if "spiral" in item and "orange":
        return "orange"
    return item


def get_ingredient(data: dict):
    """Goes over the data and extracts the ingredients."""
    num_ingr = 1
    key_ingr = "strIngredient"
    set_ingrs = set()
    item = data.get(key_ingr + str(num_ingr))
    while item:
        item = item.lower()
        item = groupify(item)
        if item != "ice":
            set_ingrs.add(item)
            WORD_SET.add(item)
        num_ingr += 1
        item = data.get(key_ingr + str(num_ingr))
    list_ingrs = list(set_ingrs)
    list_ingrs.sort()
    return list_ingrs


#########################################################################################
# Code below is from 'http://norvig.com/spell-correct.html'
# It essentially does a spellcheck on the input string and returns a spelling corrected word.
#########################################################################################


class SpellCheck:
    def __init__(self, words):
        self.words_source = Counter(list(words))

    def words(self, text):
        return re.findall(r"\w+", text.lower())

    def P(self, word):
        "Probability of `word`."
        return self.words_source[word] / sum(self.words_source.values())

    def correction(self, word):
        "Most probable spelling correction for word."
        return max(self.candidates(word), key=self.P)

    def candidates(self, word):
        "Generate possible spelling corrections for word."
        return (
            self.known([word])
            or self.known(self.edits1(word))
            or self.known(self.edits2(word))
            or [word]
        )

    def known(self, words):
        "The subset of `words` that appear in the dictionary of words_source."
        return set(w for w in words if w in self.words_source)

    def edits1(self, word):
        "All edits that are one edit away from `word`."
        letters = "abcdefghijklmnopqrstuvwxyz"
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes = [L + R[1:] for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
        replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
        inserts = [L + c + R for L, R in splits for c in letters]
        return set(deletes + transposes + replaces + inserts)

    def edits2(self, word):
        "All edits that are two edits away from `word`."
        return (e2 for e1 in self.edits1(word) for e2 in self.edits1(e1))


#########################################################################################
# Code above is from 'http://norvig.com/spell-correct.html'
# It essentially does a spellcheck on the input string and returns a spelling corrected word.
#########################################################################################


def cli():
    cookbook = get_recipe_ingredients(BASE_LIQUORS)

    trie = Trie()
    for recipe, ingrs in cookbook.items():
        trie.populate_recipes(recipe, ingrs)

    user_input = input(
        "Please enter the ingredients separated by a comma or 'exit' to end this program \n:"
    )
    spell_checker = SpellCheck(WORD_SET)
    while user_input != "exit":
        user_input = user_input.split(",")
        user_input = sorted([spell_checker.correction(x.lower()) for x in user_input])
        result = set()
        trie.search(user_input, result)
        if result:
            print(result)
        else:
            print(
                "No recipes found for given ingredients, please enter ingredients again"
            )
        user_input = input(":")


if __name__ == "__main__":
    cli()
