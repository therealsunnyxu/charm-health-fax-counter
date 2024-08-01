import pandas as pd
import string
from typing import List, Union


class NameCorrector:
    @staticmethod
    def correct_names(df: pd.DataFrame) -> pd.DataFrame:
        name_blacklist = ["Dummy", "Patient", "Sample"]
        fancy_titles = ["msn", "medical", "PhD", "phd"]
        names_df = df.copy()
        names_df = (
            names_df.apply(lambda x: [NameCorrector._unify_names(str(y)) for y in x])
            .apply(lambda x: [NameCorrector._remove_punctuations(str(y)) for y in x])
            .apply(lambda x: x.str.strip().str.replace(r"\s{2,}", " ", regex=True))
            .apply(
                lambda x: [NameCorrector._remove_words(str(y), fancy_titles) for y in x]
            )
        )
        names_df = NameCorrector._blacklist_names(names_df, name_blacklist)
        return names_df

    @staticmethod
    def _contains_any_substring(cell: str, substrings: List[str]) -> bool:
        return any(substring in cell for substring in substrings)

    @staticmethod
    def _filter_cell(cell, whitelist, blacklist, magic_word) -> bool:
        return (
            NameCorrector._contains_any_substring(cell, whitelist)
            and not NameCorrector._contains_any_substring(cell, blacklist)
            and magic_word in cell
        )

    @staticmethod
    def _filter_cols(
        col_df: pd.DataFrame, whitelist, magic_word, blacklist
    ) -> List[str]:
        filter_mapping = col_df.map(
            lambda cell: NameCorrector._filter_cell(
                cell, whitelist, blacklist, magic_word
            )
        )
        result_mapping = col_df.loc[:, filter_mapping.any()]
        filtered_cols = result_mapping.values[0].tolist()

        return filtered_cols

    @staticmethod
    def _blacklist_names(df: pd.DataFrame, blacklist) -> pd.DataFrame:
        mask = df.map(
            lambda cell: NameCorrector._contains_any_substring(cell, blacklist)
        )
        rows_to_drop = mask.any(axis=1)
        filtered_names = df[~rows_to_drop]

        return filtered_names

    @staticmethod
    def _unify_names(text: str, chars_to_unify=["'", "."], replace_char="") -> str:
        for punctuation in chars_to_unify:
            text = text.replace(punctuation, replace_char)
        return text

    @staticmethod
    def _remove_punctuations(
        text: str, replace_char=" ", dont_replace_char=["-"]
    ) -> str:
        for punctuation in [
            punct for punct in string.punctuation if punct not in dont_replace_char
        ]:
            text = text.replace(punctuation, replace_char)
        return text

    @staticmethod
    def _get_name_and_nickname(text, identifiers="{}()[]") -> Union[str, List[str]]:
        for identifier in identifiers:
            if identifier in text:
                return NameCorrector._remove_punctuations(text).split()
        return text

    @staticmethod
    def _remove_words(text: str, words_to_remove: List[str]) -> str:
        for word in words_to_remove:
            text = text.replace(word, "")

        return text
