let personFile, garmentFile;

// Hàm hiển thị ảnh khi người dùng chọn ảnh
function displayImagePreview(file, elementId) {
    const img = document.createElement('img');
    img.src = URL.createObjectURL(file);
    img.style.maxWidth = '100%';
    img.style.maxHeight = '300px';
    document.getElementById(elementId).innerHTML = '';
    document.getElementById(elementId).appendChild(img);
}

function resizeImage(file, maxWidth, maxHeight) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => {
            let width = img.width;
            let height = img.height;

            if (width > maxWidth) {
                height *= maxWidth / width;
                width = maxWidth;
            }

            if (height > maxHeight) {
                width *= maxHeight / height;
                height = maxHeight;
            }

            const canvas = document.createElement('canvas');
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, width, height);

            const quality = document.getElementById('quality').value;

            canvas.toBlob(blob => {
                resolve(new File([blob], file.name, {
                    type: file.type,
                    lastModified: file.lastModified
                }));
            }, file.type, quality); // Adjust compression quality as needed
        };
        img.onerror = reject;
        img.src = URL.createObjectURL(file);
    });
}

// Update quality value display
document.getElementById('quality').addEventListener('input', function() {
    document.getElementById('quality-value').textContent = this.value;
});

document.getElementById('try-on-btn').onclick = () => {
    const personImageInput = document.getElementById('person_image');
    const garmentImageInput = document.getElementById('garment_image');

    if (!personImageInput.files[0] || !garmentImageInput.files[0]) {
        alert("Vui lòng chọn cả hai ảnh!");
        return;
    }

    const personFile = personImageInput.files[0];
    const garmentFile = garmentImageInput.files[0];

    // Show loading indicator
    document.getElementById('loading').style.display = 'block';

    const formData = new FormData();
    formData.append('person_image', personFile);
    formData.append('garment_image', garmentFile);

    fetch('/try-on', {
        method: 'POST',
        body: formData
    })
    .then(res => {
        if (!res.ok) {
            throw new Error('Network response was not ok');
        }
        return res.json();
    })
    .then(data => {
        if (data.result_url) {
            // Hiển thị ảnh kết quả
            const outputImage = document.getElementById('output-img');
            outputImage.src = data.result_url;
            outputImage.style.display = 'block';  // Hiển thị ảnh output
        } else {
            // Hiển thị lỗi
           document.getElementById('error-text').textContent = 'Lỗi: ' + (data.error || 'Không có ảnh trả về');
           document.getElementById('error-message').style.display = 'block';
        }
        // Hide loading indicator
        document.getElementById('loading').style.display = 'none';
    })
    .catch(err => {
        console.error(err);
        document.getElementById('error-text').textContent = 'Có lỗi xảy ra, vui lòng thử lại!';
        document.getElementById('error-message').style.display = 'block';
        // Hide loading indicator
        document.getElementById('loading').style.display = 'none';
    });
};
