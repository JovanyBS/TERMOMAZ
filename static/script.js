// Basic script for modal handling and dynamic interactions

document.addEventListener('DOMContentLoaded', () => {
    // Modal handling for Tailwind-style modals (hidden/flex)
    // We attach this globally so we don't need inline onclicks everywhere if we wanted to refactor,
    // but for now we'll keep the inline onclicks calling toggleModal and just ensure toggleModal is available globally.
});

// Global function to toggle modals
window.toggleModal = function (modalID) {
    const modal = document.getElementById(modalID);
    if (modal) {
        modal.classList.toggle("hidden");
        modal.classList.toggle("flex");
    }
}

// POS Logic
let cart = [];

window.addToCart = function (id, name, price, stock) {
    const quantityInput = document.getElementById(`qty-${id}`);
    const quantity = parseInt(quantityInput.value);

    if (quantity > stock) {
        alert('No hay suficiente stock');
        return;
    }

    if (quantity <= 0) {
        alert('La cantidad debe ser mayor a 0');
        return;
    }

    const existingItem = cart.find(item => item.id === id);
    if (existingItem) {
        if (existingItem.quantity + quantity > stock) {
            alert('No hay suficiente stock para agregar más');
            return;
        }
        existingItem.quantity += quantity;
    } else {
        cart.push({ id, name, price, quantity });
    }

    updateCartUI();
    quantityInput.value = 1; // Reset input
}

window.removeFromCart = function (index) {
    cart.splice(index, 1);
    updateCartUI();
}

function updateCartUI() {
    const cartTableBody = document.getElementById('cart-items');
    const cartTotalElement = document.getElementById('cart-total');

    if (!cartTableBody || !cartTotalElement) return; // Not on POS page

    cartTableBody.innerHTML = '';
    let total = 0;

    cart.forEach((item, index) => {
        const itemTotal = item.price * item.quantity;
        total += itemTotal;

        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="py-2">${item.name}</td>
            <td class="py-2 text-center">${item.quantity}</td>
            <td class="py-2 text-right">$${itemTotal.toFixed(2)}</td>
            <td class="py-2 text-right">
                <button onclick="removeFromCart(${index})" class="text-red-500 hover:text-red-700">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        cartTableBody.appendChild(row);
    });

    cartTotalElement.textContent = total.toFixed(2);
}

window.submitOrder = async function () {
    const clientId = document.getElementById('pos-client-id').value;
    if (!clientId) {
        alert('Por favor seleccione un cliente');
        return;
    }

    if (cart.length === 0) {
        alert('El carrito está vacío');
        return;
    }

    try {
        const response = await fetch('/pos/create_order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                client_id: clientId,
                items: cart
            })
        });

        const result = await response.json();

        if (result.success) {
            alert('Pedido creado exitosamente!');
            window.location.href = `/orders/${result.order_id}`;
        } else {
            alert('Error al crear pedido: ' + result.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Ocurrió un error al procesar el pedido');
    }
}
