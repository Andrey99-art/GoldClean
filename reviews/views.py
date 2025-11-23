from django.shortcuts import render, redirect
from .forms import ReviewForm

def leave_review(request):
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            # ВАЖНО: Новый отзыв по умолчанию неактивен
            review.is_active = False
            review.save()
            return redirect('review_success')
    else:
        form = ReviewForm()
        
    return render(request, 'reviews/leave_review.html', {'form': form})

def review_success(request):
    return render(request, 'reviews/review_success.html')