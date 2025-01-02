from django import forms

import pydb


class SearchForm(forms.Form):
    query = forms.CharField(label="Search", max_length=100, required=False)
    principal_language = forms.ChoiceField(label="", choices=[], required=False)
    tome_type=forms.ChoiceField(label="", choices=[])

    def __init__(self, *args, pdb=None, **kwargs):
        super().__init__(*args, **kwargs)

        lang_list = pdb.get_used_languages()
        if "" not in lang_list:
            lang_list = [""] + lang_list
        lang_tuples = [(lang, lang if lang !="" else "don't care") for lang in lang_list]
        self.fields["principal_language"].choices = lang_tuples

        self.fields["tome_type"].choices=[
            (pydb.TomeType.Fiction, 'Fiction'),
            (pydb.TomeType.NonFiction, 'Non-Fiction'),
            ("Z", "Don't Care")
        ]

    def build_search_query(self):
        generated_query = self.cleaned_data.get('query')

        principal_language = self.cleaned_data.get('principal_language')
        if principal_language:
            generated_query += " principal_language:%s" % principal_language

        tome_type = self.cleaned_data.get('tome_type')
        if tome_type:
            if tome_type != "Z":
                generated_query += " type:%s" % tome_type

        return generated_query