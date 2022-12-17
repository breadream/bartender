import unittest

from unittest.mock import patch, mock_open

from recipe_finder import Trie, get_ingredient, get_recipe_ingredients, load_drink_data


class TestRecipeFinder(unittest.TestCase):
    def setUp(self):
        self.trie_obj = Trie()
        self.ingr_data = {
            "idDrink": "13196",
            "strDrink": "Long vodka",
            "strIngredient1": "Vodka",
            "strIngredient2": "Lime",
            "strIngredient3": "Angostura bitters",
            "strIngredient4": "Tonic water",
            "strIngredient5": "Ice",
            "strIngredient6": None,
            "strIngredient7": None,
            "strIngredient8": None,
        }
        self.ingr_data_2 = {
            "idDrink": "14444",
            "strDrink": "Short vodka",
            "strIngredient1": "Vodka",
            "strIngredient2": "Sweets",
            "strIngredient3": "Tonic water",
            "strIngredient4": None,
            "strIngredient5": None,
        }

    def test_trie_search(self):
        self.trie_obj.populate_recipes(
            "pizza", sorted(["cheese", "flour", "water", "tomato"])
        )
        self.trie_obj.populate_recipes("dough", sorted(["water", "flour"]))
        res = set()
        self.trie_obj.search(sorted(["cheese", "flour", "water", "tomato"]), res)
        self.assertEqual(res, {"dough", "pizza"})

    def test_trie_search_only_one_ingredient(self):
        self.trie_obj.populate_recipes(
            "pizza", sorted(["cheese", "flour", "water", "tomato"])
        )
        self.trie_obj.populate_recipes("grilled cheese", sorted(["cheese", "bread"]))
        res = set()
        self.trie_obj.search(sorted(["cheese", "flour", "water", "tomato"]), res)
        self.assertNotIn("grilled cheese", res)

    def test_get_ingredients(self):
        ingr_list = get_ingredient(self.ingr_data)
        expected_result = ["bitters", "lime", "tonic water", "vodka"]
        self.assertEqual(expected_result, ingr_list)

    @patch("os.access")
    @patch("os.path.isfile")
    def test_load_drink_data_file_readable_and_exists(
        self, mock_os_path_isfile, mock_os_access
    ):
        mock_os_path_isfile.return_value = True
        mock_os_access.return_value = True
        with self.assertLogs(level="INFO") as cm:
            load_drink_data(["liquor1", "liquor2"])
            self.assertEqual(cm.output[-1], "INFO:root:Drink data file already exists")

    @patch("recipe_finder.get_liquor_recipes")
    @patch("json.dump")
    @patch("os.access")
    @patch("os.path.isfile")
    def test_load_drink_data_no_file(
        self,
        mock_os_path_isfile,
        mock_os_access,
        mock_json_dump,
        mock_get_liquor_recipes,
    ):
        mock_os_path_isfile.return_value = False
        mock_os_path_isfile.return_value = False
        with self.assertLogs(level="INFO") as cm:
            load_drink_data(["liquor1", "liquor2"])
            self.assertEqual(
                cm.output[-1],
                "INFO:root:Either file is missing or is not readable, generating file...",
            )

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    @patch("recipe_finder.load_drink_data")
    def test_get_recipe_ingredients(
        self, mock_load_drink_data, mock_json_load, mock_open
    ):
        mock_json_load.return_value = {"vodka": [self.ingr_data, self.ingr_data_2]}
        expected_result = {
            "Long vodka": ["bitters", "lime", "tonic water", "vodka"],
            "Short vodka": ["sweets", "tonic water", "vodka"],
        }
        result = get_recipe_ingredients(["vodka"])
        self.assertEqual(expected_result, result)
