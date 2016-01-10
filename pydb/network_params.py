# coding=utf-8
# fidelity values of documents received from friends will be reduced by this values before
# we display it as our opinion,
# needs to larger than 0 or the network will degrade
Friend_Fidelity_Deduction = 5.0

# sometimes we need to transfer an author or a tome from merge db to local db, shall we reduce fidelity when doing this?
Fidelity_Deduction_Auto_Create = 0.1

# if the fidelity is below this value, the data won't be displayed/transferred and is considered deleted
Min_Relevant_Fidelity = 20

# if a manually triggered action needs a fidelity, this value is used as a default
Default_Manual_Fidelity = 80


def is_relevant(entry):
    return entry['fidelity'] >= Min_Relevant_Fidelity


def relevant_items(iterable):
    return (i for i in iterable if is_relevant(i))


def link_is_relevant(entry):
    return entry['link_fidelity'] >= Min_Relevant_Fidelity


def relevant_links(iterable):
    return (i for i in iterable if link_is_relevant(i))

