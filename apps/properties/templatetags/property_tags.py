from django import template

register = template.Library()

@register.filter(name='indian_currency')
def indian_currency(value):
    if value is None:
        return 'Price on Request'
    try:
        val = float(value)
    except (ValueError, TypeError):
        return str(value)

    if val >= 10000000:
        cr = val / 10000000.0
        return f"₹ {cr:.2f} Cr"
    elif val >= 100000:
        lakhs = val / 100000.0
        return f"₹ {lakhs:.2f} Lakhs"
    elif val >= 1000:
        return f"₹ {val:,.0f}"
    else:
        return f"₹ {val:.0f}"

@register.filter(name='indian_rent')
def indian_rent(value):
    if value is None:
        return 'On Request'
    try:
        val = float(value)
    except (ValueError, TypeError):
        return str(value)
    if val >= 100000:
        lakhs = val / 100000.0
        return f"₹ {lakhs:.2f} Lakhs / mo"
    else:
        return f"₹ {val:,.0f} / mo"
