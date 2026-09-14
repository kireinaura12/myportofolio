Nama : Kireina Naura Alifa
NPM : 2506590006
Kelas : PBP D

### Tugas 1
1. Ya, saya menggunakan <section> dalam tugas 1, namun tidak menggunakan <aside> dan <article>. <section> membantu saya mengelompokkan bagian content dari web statis ini, dimana content web saya terbagi menjadi 3 yaitu hero, profile dan projects.
2. Tantangan tersulitnya adalah saat mengatur ulang tata letak profile untuk tampilan mobile. Karena profile memiliki banyak bagian, saya memutuskan untuk memprioritaskan profile-kicker dan profile-photo. Selain itu, saya juga memutuskan untuk merubah layout project card dari yang sebelumnya landscape menjadi potrait, lalu menambahkan fitur slide carousel agar tampilan mobile tetap terbaca
3. Menambahkan bagian-bagian yang kemungkinan besar kedepannya akan ada update seperti experience dan projects. Oleh karena itu saya ingin ada fitur menambah experience dan projects tanpa harus hardcode lagi

### Tugas 2
1. Ketika user membuka halaman portofolio, browser akan mengirim request ke project Django. Lalu urls.py proyek akan menentukan aplikasi mana yang menangani request tersebut. Setelah diarahkan ke urls.py aplikasi, URL akan dicocokkan dengan pola URL yang ada dan diarahkan ke view yang dituju. Llau view akan mengambil data yang diperlukan di model, dimana model menjadi representasi struktur data yang tersimpan di database. Setelah mendapatkan data, view mengirim ke template melalui context. Kemudian template menggabungkan data tersebut dengan struktur HTML yang sudah dibuat.
2. Karena dengan model kita dapat dengan mudah menambah, menghapus, ataupun mengubah data, tanpa harus mengubah struktur html. Kedepannya ini juga akan memudahkan pemeliharaan dan pengembangan aplikasi seiring bertambahnya data 
3. makemigrations digunakan untuk membuat file migration berdasarkan perubahan pada models.py. Sedangkan migrate digunakan untuk menerapkan instruksi dari file migration tersebut ke database. Contohnya ketika saya ingin mengubah field thumbnail bawaan dari tutorial 2 kemarin. Karena saya mengubah struktur database-nya, maka saya perlu menjalankan makemigrations dan migrate

# AI Disclosure
Dalam pengerjaan project ini, saya menggunakan:
Chatgpt:
- untuk memahami konsep models, field, django admin, dan banyak istilah baru yang muncul di materi pekan ini
Claude.ai: 
- membantu melakukan debugging
- memberikan saran terkait struktur HTML dan CSS
- membantu dalam menyesuaikan layout tampilan web khususnya agar responsive pada mobile
- menambahkan hover yang lebih menarik