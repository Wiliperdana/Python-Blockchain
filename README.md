# Python Blockchain

Pengembangan Blockchain Menggunakan Python Pada Jaringan Lokal


# Installation
### Clone the repository:
```
git clone https://github.com/Wiliperdana/Python-Blockchains.git
```

### Pindah ke directory Python-Blockchains:
```
cd Python-Blockchains
```

### Install dependency:
```
pip install flask
pip install requests
```

### Jalankan Project Dengan 2 Terminal Berbeda:
Buka terminal yang pertama, lalu jalankan command berikut
```
python blockchains.py 5000
```

Kemudian buka terminal yang kedua dan jalankan command berikut
```
python blockchains.py 5001
```

# Testing:

### Postman
1. Buka Postman:
Export file **Blockchain.postman_collection.json**

2. Testing Blockchain:
Buka folder **Blockchain** di Postman.
Pilih request **Get Blockchain 1** dan klik **Send**.
Pastikan untuk mencatat respons yang diberikan.
Pilih request **Get Blockchain 2** dan klik **Send**.
Respons yang muncul akan serupa dengan respons dari **Get Blockchain 1**.

3. Menambahkan Node:
Buka folder **Nodes** di Postman.
Pilih request **Add Nodes 1** dan klik **Send**.
Pilih request **Add Nodes 2** dan klik **Send**.
Ini akan membuat dua node yang dijalankan pada dua instansi proyek yang berbeda.

4. Menambahkan Transaksi:
Kembali ke folder **Blockchain**.
Pilih request **Transaction 1** dan klik **Send**.
Coba jalankan request **Get Blockchain 1** dan **Get Blockchain 2**.
Hasilnya belum berubah karena transaksi belum di-mining.

5. Mining:
Pilih request **Mining 1** dan klik **Send**.
Jalankan kembali request **Get Blockchain 1**.
Respons sekarang sudah diperbarui.
Jalankan request **Get Blockchain 2**.
Respons belum berubah karena node belum disinkronisasi.

6. Sinkronisasi Nodes:
Kembali ke folder **Nodes**.
Pilih request **Sync Node 1** dan klik **Send**.
Pilih request **Sync Node 2** dan klik **Send**.
Kedua request ini berfungsi untuk sinkronisasi nodes satu sama lain.

Jalankan kembali request **Get Blockchain 2**.
Sekarang respons sudah sama dengan **Get Blockchain 1**.