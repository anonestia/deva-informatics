# DEVA PROJECT
##### Discord AI Chatbot specified for tutoring informatics student.

Ini adalah proyek pembuatan sebuah **AI Chatbot** untuk kebutuhan pendidikan, khususnya Informatika. AI sudah bisa membantu banyak mahasiswa Informatika untuk menyelesaikan tugas-tugas program serta membantu memberikan "kelas" tambahan di luar jam pembelajaran.

Namun, *sudah kah maksimal penggunaan AI Chatbot untuk mahasiswa?*

**Deva** adalah AI chatbot yang akan membawa fitur-fitur baru untuk memaksimalkan penggunaan kecerdasan buatan. Nama "Deva" berasal dari ***Developer-A***, dengan A adalah kelas dari tim pengembang AI chatbot ini. Hal utama pada proyek ini adalah

#### AI Chatbot yang dipersonalisasi sehingga mendukung berjalannya pembelajaran mahasiswa dengan AI yang adaptif serta memahami pengguna, berbicara dengan natural, dan dapat dianggap sebagai teman, bukan sekadar alat.

Fitur akan terus ditambahkan secara berkala, namun masih perlahan karena sedikitnya anggota tim pengembang. Platform yang digunakan sekarang hanya **Discord** dan akan dibuat lebih luas.


## Apa yang membuat Deva berbeda dari AI Chatbot lainnya?
Ada beberapa kunci yang membuat Deva berbeda, yaitu:
- AI yang **memiliki kepribadiannya** sendiri, sehingga dapat berbicara dengan natural dan lebih *friendly*.
- Kemampuan menyimpan **memori dan database** khusus yang dapat ditarik sewaktu-waktu untuk mendapatkan informasi yang tidak ada pada umum (akan dijelaskan di bawah).
- Pengguna, mahasiswa maupun dosen, dapat membuat perubahan interaksi kepada mereka secara khusus dengan **mengubah profil pengguna**. Beritahu kepada Deva apa yang perlu ketahui. Bagaimana Deva harus berinteraksi, kesulitanmu dalam pembelajaran, proyek yang sedang kamu kerjakan, dan hal lainnya.

Hal-hal ini bisa jadi telah ada sebelumnya, namun belum dikhususkan untuk pendidikan maupun dipersonalisasi sejauh ini untuk satu-satunya tujuan tersebut.



## Fitur-Fitur yang Diimplementasikan
Berikut adalah daftar fitur yang *sudah dan akan* diimplementasikan kepada Deva.

### I. Dasar AI Chatbot
Hal-hal yang membuat chatbot adalah chatbot, dan Deva adalah Deva.
- [x] Kemampuan membedakan tiap channel di server serta membedakan chat channel dengan DM.
    > Dengan membedakan tempat chat, Deva tidak akan keliru dengan riwayat chat yang lain. Kemampuan dasar dan wajib untuk chatbot yang dapat secara dinamis mengobrol tanpa command terlebih dahulu.
- [ ] Mendapatkan konteks dari channel lain di server yang sama
    > Dibutuhkan apabila ada channel penting yang bisa Deva rujuk sebagai informasi, termasuk aturan, pengumuman, dan berita. (Bisa jadi, apabila ada server pusat kampus, Deva bisa selalu mengambil konteks dari channel di server tersebut untuk mendapatkan berita resmi.)
- [ ] Mendapatkan konteks dari pesan yang di-reply oleh pengguna
    > Untuk memaksimalkan penerimaan konteks apabila pengguna merujuk pada sebuah pesan selain dari pesan terbaru, tanpa mengucapkan kembali isi pesan tersebut.
- [x] Inisiatif memasuki percakapan yang sedang ramai.
    > Deva dapat secara inisiatif mengikuti percakapan dan menanggapi bahasan yang sedang ada. Hal ini diimplementasikan untuk menambah nilai natural dan mendapatkan pendekatan kepada mahasiswa.
- [ ] Kemampuan menerima dan memberikan *reaction* pada sebuah pesan.
    > Apabila pengguna memberikan sebuah *reaction* (emoji) pada sebuah pesan, Deva akan merekamnya. Apabila pengguna melakukannya pada pesan Deva, maka Deva bisa jadi akan menanggapi hal tersebut. Deva memiliki kemungkinan untuk memberikan *reaction* pula kepada pesan pengguna.
- [ ] Memiliki ***emoji Deva*** untuk digunakan.
    > Berbeda dengan emoji default, emoji khusus Deva menambah kesan hidup dan ekspresif, sehingga menjadi chatbot yang unik dan *memorable* bagi pengguna. Dapat membuat mahasiswa lebih nyaman dalam menggunakan dan dekat dengan Deva.

### II. Knowledge, Local Database
Kemampuan penyimpanan informasi khusus yang tidak ada pada training AI default.
- [x] Memiliki local database berisikan informasi khusus yang tidak diwarisi oleh AI.
    > Informasi spesifik tentang kelas, jadwal, mata kuliah, dan prosedur-prosedur di sekitar kampus yang hanya bisa didapatkan apabila didapatkan secara real-time dapat disimpan pada local database AI untuk dijadikan referensi pada kondisi yang tepat.
    - [x] Pembuatan command untuk input **knowledge**
        > Command dibuat untuk mempermudah proses CRUD knowledge, sehingga pemeliharaan data mudah.
    - [x] Pembuatan sistem penarikan **knowledge** dengan dua cara: Kondisi dan Keyword (kata kunci)
        > Membedakan cara penarikan antara beberapa knowledge akan memaksimalkan *user experience*. Tidak semua pertanyaan akan selalu mendapat kata kunci yang tepat, sehingga penggunaan penarikan kondisi dengan bantuan AI akan menambah ketepatan dalam penarikan.
    - [x] Error-Handling apabila tidak ditemukan knowledge yang tepat untuk menghindari halusinasi.

### III. Profil Pengguna
Kustomisasi lanjutan berupa profil pengguna untuk penyesuaian respon.
- [x] Mengizinkan pengguna untuk memberitahukan Deva informasi yang perlu diketahui Deva, diantaranya:
    - **Nama panggilan**
    - **Posisi** (mahasiswa atau dosen. Bisa menambahkan seperti mahasiswa informatika atau dosen logika dan komputasi.)
    - **Semester** dan **Kelas** bagi mahasiswa
    - **Tentang** (kanvas untuk pengguna berbagi tentang dirinya serta mengatur cara tanggapan Deva khusus padanya)
- [x] Penarikan informasi penuh bagi yang meng-*trigger* respon, dan sebagian informasi bagi pengguna lain.
    > Pengguna yang bukan memberikan *trigger* untuk Deva membalas tidak akan ditarik "tentang"-nya. Contoh, ada A, B, dan C sedang berbicara satu sama lain. Lalu, B melakukan mention `@Deva` dan bertanya kepada Deva di pesan yang sama. "Tentang" yang ditarik hanyalah milik B, namun konteks lain soal siapa A dan C akan tetap dimasukkan.
- [x] Penarikan informasi penuh apabila sebuah user di-mention `<@ID>` pada sebuah chat sekaligus trigger balasan Deva.
    > Ini adalah sebuah pengecualian di mana informasi pengguna yang bukan trigger diterima secara penuh untuk dapat memahami penuh pengguna yang dirujuk.
- [x] Kemampuan menyimpan **long-term memory** khusus pada sebuah pengguna.
    > Untuk dapat menyimpan informasi secara dinamis tentang pengguna, maka menambahkan long-term memory akan sangat membantu kostumisasi lanjutan tanpa pengguna perlu menuliskannya manual. Long-term memori memiliki cara penarikan yang serupa dengan knowledge dibandingkan dengan kostumisasi.

### IV. File dan Gambar
- [ ] Kemampuan untuk memahami gambar (vision)
- [ ] Kemampuan untuk membaca file tertentu.
    > Utamanya adalah file coding seperti .py, .java, .c, dan lainnya yang dipakai pada jurusan Informatika.
- [ ] Kemampuan membuat tabel dan grafik dengan library khusus (bukan gambar AI generate) dan mengirimnya.
    > Tabel dapat digunakan untuk daftar seperti jadwal, nama dosen terkait, dan lainnya yang ada pada knowledge. Hal ini dilakukan supaya tim tidak perlu memperbaharui gambar satu persatu, melainkan cukup mengubah knowledge. Pengolahan data tetap menggunakan AI sebelum dikirimkan ke library manipulasi gambar.
- [ ] Kemampuan membuat, menyunting, dan mengirimkan file ke chat.