# extract_health_name.py

def extract_health_name(name):
    """
    Extracts health type based on animal names found in the input string.
    """
    name_lower = name.lower()

    inhibitory = ['a', 'b', 'c', 'f', 'e', 'l', 'g', 'h', 'i', 'j', 'k', 'o', 'm', 'p', 'q']
    ghrelin = ['ftworth', 'orlando', 'tampa', 'dallas', 'la', 'seattle', 'chicago',
               'lascruces', 'tokyo', 'ruidoso', 'neworleans', 'atlanta', 'newyork', 'newjersey']
    saline = ['austin', 'houston', 'toronto', 'berlin', 'denver', 'elpaso', 'waco',
              'lisbon', 'nairobi', 'rome', 'venice', 'paris', 'london', 'phoenix']
    excitatory = ['dopey', 'sneezy', 'doc', 'grumpy', 'sleepy', 'bashful', 'happy',
                  'sam', 'roy', 'ivy', 'may']

    # Split name into underscore-separated tokens for accurate matching
    tokens = name_lower.split('_')

    # Priority-based matching
    if any(token in inhibitory for token in tokens):
        return 'Inhibitory'
    elif any(token in ghrelin for token in tokens):
        return 'Ghrelin'
    elif any(token in saline for token in tokens):
        return 'Saline'
    elif any(token in excitatory for token in tokens):
        return 'Excitatory'
    else:
        return 'Unknown'
