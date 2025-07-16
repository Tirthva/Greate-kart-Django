from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from .models import Cart, CartItem
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist  # <-- Add this import


# Create your views here.

def _cart_id(request):
    cart_id = request.session.session_key
    if not cart_id:
        cart_id = request.session.create()
    return cart_id

def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)  # get the product by id
    product_variation = [] # to store the variations of the product
    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]

            try:
                variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                product_variation.append(variation)  # add the variation to the list
            except:
                pass

    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))  # get the cart by id
    except Cart.DoesNotExist:
        cart = Cart.objects.create(cart_id=_cart_id(request))
    cart.save()
 
    is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
    if is_cart_item_exists:
        cart_item = CartItem.objects.filter(product=product, cart=cart)
        # extracting the variations of the product
        # if the product has variations = current variations
        # item id
        ex_var_list = []
        id = []
        for item in cart_item:
            existing_variations = item.variations.all()
            ex_var_list.append(list(existing_variations))
            id.append(item.id)

        print(ex_var_list)

        if product_variation in ex_var_list:
            # increment the quantity
            index = ex_var_list.index(product_variation)
            item_id = id[index]
            item = CartItem.objects.get(product=product, id=item_id)
            item.quantity += 1
            item.save()

        else:
            item = CartItem.objects.create(product=product, cart=cart, quantity=1)
            if len(product_variation) > 0:
                item.variations.clear()  # clear existing variations
                item.variations.add(*product_variation)  # add new variations
            item.save()
            
    else:
        item = CartItem.objects.create(product=product, cart=cart, quantity=1)
        if len(product_variation) > 0:
            item.variations.clear()  # clear existing variations
            item.variations.add(*product_variation)  # add new variations
        item.save()
    return redirect('cart')  # redirect to the cart view

def remove_cart(request, product_id, cart_item_id ):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)  # get the product by id
    try:
        cart_item = CartItem.objects.get(product=product, id=cart_item_id, cart=cart)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1  # decrement the quantity
            cart_item.save()
        else:
            cart_item.delete()  # remove the item if quantity is 1
    except:
        pass
    return redirect('cart')

def remove_cart_item(request, product_id, cart_item_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)  # get the product by id
    cart_item = CartItem.objects.get(product=product, id=cart_item_id, cart=cart)
    cart_item.delete()  # delete the cart item
    return redirect('cart')  # redirect to the cart view


def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        # Get the cart items for the current session
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)  # <-- Use is_active
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total) / 100  # Assuming a tax rate of 5%
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass  # If the cart does not exist, we simply pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total
    }
    return render(request, 'store/cart.html', context)