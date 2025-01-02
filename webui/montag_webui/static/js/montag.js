

function saveFormIfControlSPressed(event) {
    if (event.ctrlKey || event.metaKey) {
        var letter = String.fromCharCode(event.which).toLowerCase();
        if(letter == 's') {
            event.preventDefault();
            document.forms[0].submit();
        }
    }
}