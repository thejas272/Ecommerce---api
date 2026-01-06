

# queryset => cart itmes


def calculate_checkout_price(queryset):
    subtotal = sum(cart_item.total_price for cart_item in queryset)

    shipping_fee = 0 if subtotal >= 500 else 99

    grand_total = subtotal + shipping_fee

    return subtotal,shipping_fee,grand_total