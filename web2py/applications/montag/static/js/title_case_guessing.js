function uc_first_only(a) {
    return a.substr(0,1).toUpperCase() + a.substr(1).toLowerCase();
}

var lowercase_words = new Array("to","a","an","the","at","in","with","and","but","or")

function word_remains_lowercase(word)
{
    var i;

    for(i=0; i< lowercase_words.length; i++) {
        if(word == lowercase_words[i]) return true;
    }
    return false;
}

function title_case(text) {
	var result = ''

	var words = text.split(' ');
        var i;
	for (i=0; i<words.length; i++) {
		var word=words[i].toLowerCase();
                if(i!=0 && word_remains_lowercase(word)) {
                    word=word.toLowerCase();
                } else {
                    word=uc_first_only(word)
                }

		if (result != '') result += ' ';
		result += word;
	}

	return result;
}


function title_case_field(id) {
    el = document.getElementById(id)
    el.value = title_case(el.value)
}
