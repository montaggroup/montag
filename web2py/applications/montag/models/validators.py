class TagValidator:
    def __init__(self, format="a", error_message="b"):
        pass
        
    def __call__(self, field_value):
        used_tag_values = set()
        tags = []
        
        field_value = field_value.decode('utf-8')
        for line_index, line in enumerate(field_value.split("\n")):
            line = line.strip()
            if line:
                fidelity = pydb.network_params.Default_Manual_Fidelity
                value = line
                if " " in line:
                    (fidelity_string, value_string) = line.split(" ",1)
                    try:
                        fidelity = float(fidelity_string)
                        value = value_string
                    except ValueError:
                        pass
                
                value = value.strip()
                if value in used_tag_values:
                    return None, u"Duplicate tag names entered: {}".format(value)
                used_tag_values.add(value)
                tags.append({"fidelity":fidelity, "tag_value" : value})
        return tags, None
     
    def formatter(self, value):
        tags = value
        return "\n".join(["%.1f %s" %(tag['fidelity'], tag['tag_value'].encode('utf-8')) for tag in tags])


class FidelityValidator:
    def __init__(self, format="a", error_message="b"):
        pass

    def __call__(self, field_value):
        fidelity = float(field_value)
        if fidelity < -100:
            return None, u('Fidelity must be at least -100.');
        if fidelity > 100:
            return None, u('Fidelity must be at max 100.');

        return fidelity, None

    def formatter(self, value):
        return "{:.1f}".format(value)


class AuthorValidator:
    def __init__(self, format='a', error_message='b'):
        pass

    def __call__(self, field_value):
        authors=set()
        authors_list=[]
        
        field_value=field_value.decode('utf-8')
        for line in field_value.split('\n'):
            author_name = line.strip()
            if author_name:
                if author_name in authors:
                    return None, u'Duplicate author names entered: {}'.format(author_name)
                authors.add(author_name)
                authors_list.append(author_name)

        if not authors:
            return None,'Empty author field'
        return authors_list, None

    def formatter(self, value):
        authors = value
        return '\n'.join([author['name'].encode('utf-8') for author in authors])
