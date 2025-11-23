# accounts/views.py

from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView
from .forms import RegistrationForm
from orders.forms import OrderFullEditForm
from orders.models import Order
from products.models import Service, AdditionalService
from core.models import SiteConfiguration
from django.utils import timezone
from datetime import timedelta, datetime
from .models import Profile


def _calculate_order_total_price(order_instance, additional_services_qs):
    service = order_instance.service
    total_price = service.base_price

    if service.is_sqm_based:
        total_price += (order_instance.sqm or 0) * service.price_per_sqm
    else:
        total_price += max(0, (order_instance.rooms_count or 1) - 1) * service.price_per_room
        total_price += max(0, (order_instance.bathrooms_count or 1) - 1) * service.price_per_bathroom

    total_price += sum(s.price for s in additional_services_qs)

    if order_instance.bring_vacuum_cleaner:
        total_price += Decimal(settings.VACUUM_CLEANER_PRICE)
    
    if order_instance.is_private_house:
        total_price *= Decimal('1.2')
    
    discounts = {'monthly': 0.10, 'bi_weekly': 0.15, 'weekly': 0.20}
    if order_instance.frequency in discounts:
        discount_amount = total_price * Decimal(discounts[order_instance.frequency])
        total_price -= discount_amount
            
    return total_price


class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('index')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        login(self.request, user)
        
        message_text = _("You have registered successfully. Welcome, {username}!").format(username=user.username)
        messages.success(self.request, message_text)
        
        return response


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    profile, created = Profile.objects.get_or_create(user=request.user)
    context = {
        'orders': orders,
        'penalty_balance': profile.penalty_balance, # <-- Передаем баланс в шаблон
    }
    return render(request, 'accounts/order_list.html', context)


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {
        'order': order
    }
    return render(request, 'accounts/order_detail.html', context)


@login_required
def order_edit(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status in ['completed', 'canceled']:
        messages.error(request, _("This order can no longer be edited."))
        return redirect('order_detail', order_id=order.id)

    if request.method == 'POST':
        form = OrderFullEditForm(request.POST, instance=order)
        if form.is_valid():
            additional_services = form.cleaned_data['additional_services']
            
            # Обновляем поля существующего объекта 'order' из формы.
            order.service = form.cleaned_data['service']
            order.rooms_count = form.cleaned_data['rooms_count']
            order.bathrooms_count = form.cleaned_data['bathrooms_count']
            order.sqm = form.cleaned_data['sqm']
            order.bring_vacuum_cleaner = form.cleaned_data['bring_vacuum_cleaner']
            order.is_private_house = form.cleaned_data['is_private_house']
            order.cleaning_date = form.cleaned_data['cleaning_date']
            order.cleaning_time = form.cleaned_data['cleaning_time']
            order.comments = form.cleaned_data['comments']

            order.total_price = _calculate_order_total_price(order, additional_services)
            order.save()
            order.additional_services.set(additional_services)

            messages.success(request, _("Order has been updated successfully."))
            return redirect('order_detail', order_id=order.id)
    else:
        form = OrderFullEditForm(instance=order)

    all_additional_services = AdditionalService.objects.filter(is_active=True)
    return render(request, 'accounts/order_edit.html', {
        'form': form,
        'order': order,
        'all_additional_services': all_additional_services
    })


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Запрещаем отменять уже выполненные или отмененные заказы
    if order.status in ['completed', 'canceled']:
        messages.error(request, _("This order can no longer be canceled."))
        return redirect('order_detail', order_id=order.id)

    # --- ЛОГИКА ПРОВЕРКИ ВРЕМЕНИ ---
    config = SiteConfiguration.get_solo()
    penalty_fee = config.cancellation_fee
    
    # Создаем aware datetime объект для времени уборки
    cleaning_datetime = timezone.make_aware(
        datetime.combine(order.cleaning_date, order.cleaning_time)
    )
    time_until_cleaning = cleaning_datetime - timezone.now()
    
    is_penalty_period = time_until_cleaning < timedelta(hours=24)

    if request.method == 'POST':
        # Пользователь подтвердил отмену
        order.status = 'canceled'
        if is_penalty_period:
             # Получаем профиль пользователя
            profile, created = Profile.objects.get_or_create(user=request.user)
            # Добавляем штраф к его балансу
            profile.penalty_balance += penalty_fee
            profile.save()
            # Добавляем системный комментарий о штрафе
            penalty_note = _("\n\n[System] Canceled with a penalty of {fee} zł.").format(fee=penalty_fee)
            order.comments = (order.comments or "") + penalty_note
            messages.warning(request, _("A penalty of {fee} zł has been added to your account balance.").format(fee=penalty_fee))
        
        
        order.save()
        messages.success(request, _("Order #{id} has been successfully canceled.").format(id=order.id))
        return redirect('order_list')

    context = {
        'order': order,
        'is_penalty_period': is_penalty_period,
        'penalty_fee': penalty_fee,
    }
    return render(request, 'accounts/cancel_order_confirm.html', context)