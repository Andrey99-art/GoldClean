window.addEventListener("load", function() {
    // Ждем, пока Django загрузит инлайн-формы
    django.jQuery(document).on('formset:added', function(event, $row, formsetName) {
        if (formsetName === 'feature_points') {
            // Очищаем поля при добавлении новой точки
            $row.find('input[name$="-position_x"]').val('');
            $row.find('input[name$="-position_y"]').val('');
        }
    });

    const imagePreview = document.getElementById('hotspot-image-preview');
    if (imagePreview) {
        imagePreview.addEventListener('click', function(e) {
            // Находим последнюю пустую инлайн-форму для точек
            const lastEmptyRow = django.jQuery('.dynamic-feature_points:not(.has_original)').last();
            
            if (lastEmptyRow.length === 0) {
                alert('Пожалуйста, сначала нажмите "Add another Feature Point"');
                return;
            }

            const rect = imagePreview.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const x_percent = (x / rect.width * 100).toFixed(1);
            const y_percent = (y / rect.height * 100).toFixed(1);

            // Заполняем поля в найденной строке
            lastEmptyRow.find('input[name$="-position_x"]').val(x_percent);
            lastEmptyRow.find('input[name$="-position_y"]').val(y_percent);

            // Визуальный индикатор клика
            const clickIndicator = document.createElement('div');
            clickIndicator.style.position = 'absolute';
            clickIndicator.style.left = x_percent + '%';
            clickIndicator.style.top = y_percent + '%';
            clickIndicator.style.width = '15px';
            clickIndicator.style.height = '15px';
            clickIndicator.style.background = 'red';
            clickIndicator.style.borderRadius = '50%';
            clickIndicator.style.transform = 'translate(-50%, -50%)';
            clickIndicator.style.pointerEvents = 'none';
            imagePreview.parentElement.style.position = 'relative';
            imagePreview.parentElement.appendChild(clickIndicator);
            setTimeout(() => clickIndicator.remove(), 1000);
        });
    }
});