from django.conf import settings

from product.models import Product


class Item:
    def __init__(self, product_id, quantity):
        self._product_id = product_id
        self._quantity = quantity
    
    def get_product_id(self):
        return self._product_id
    
    def set_product_id(self, product_id):
        self._product_id = product_id
    
    def get_quantity(self):
        return self._quantity
    
    def set_quantity(self, quantity):
        self._quantity = quantity
    
    def copy(self):
        return Item(self._product_id, self._quantity)


class CartItem(Item):
    def __init__(self, product_id, quantity):
        super().__init__(product_id, quantity)
        self._product = None
    
    def get_product(self):
        return self._product
    
    def set_product(self, product):
        self._product = product
        
    def copy(self):
        item_copy = super().copy()
        cart_item_copy = CartItem(item_copy.get_product_id(), item_copy.get_quantity())
        cart_item_copy.set_product(self.get_product())
        return cart_item_copy


class Cart(object):
    def __init__(self, request):
        self._session = request.session
        cart = self._session.get(settings.CART_SESSION_ID)

        if not cart:
            cart = self._session[settings.CART_SESSION_ID] = {}
        
        self._cart = cart
    
    def __iter__(self):
        for p in self._cart.keys():
            cart_item = CartItem(self._cart[p]['id'], self._cart[p]['quantity'])
            cart_item.set_product(Product.objects.get(pk=cart_item.get_product_id()))
            self._cart[str(p)] = cart_item.copy().__dict__
    
    def __len__(self):
        return sum(item['quantity'] for item in self._cart.values())
    
    def save(self):
        self._session[settings.CART_SESSION_ID] = self._cart
        self._session.modified = True
    
    def add(self, product_id, quantity=1, update_quantity=False):
        product_id = str(product_id)

        if product_id not in self._cart:
            cart_item = CartItem(product_id, 1)
            cart_item.set_product(Product.objects.get(pk=cart_item.get_product_id()))
            self._cart[product_id] = cart_item.__dict__
        else:
            cart_item = CartItem(self._cart[product_id]['id'], self._cart[product_id]['quantity'])
            cart_item.set_product(Product.objects.get(pk=cart_item.get_product_id()))
            if update_quantity:
                cart_item.set_quantity(int(quantity))
            else:
                cart_item.set_quantity(cart_item.get_quantity() + int(quantity))
                
            if cart_item.get_quantity() == 0:
                self.remove(product_id)
            else:
                self._cart[product_id] = cart_item.__dict__
            
        self.save()
    
    def remove(self, product_id):
        if product_id in self._cart:
            del self._cart[product_id]
            self.save()
