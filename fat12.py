import os, hashlib

fd = os.open('fat.0590.img', os.O_RDWR)

def file_as_bytes(file):
    with file:
        return file.read()

def next_cluster(fd, fat_offset, current):
    data = lseek_file(fd, fat_offset + ((current % 2) + (current // 2) * 3), 2)
    return data & 0x0fff if (current % 2) == 0 else data >> 4

def for_root(fd, root_offset, list_count, cluster_count, sector_size, fat_offset, data_offset, f_name_list=[], all_sum=b''):
    for i in range(list_count):
        record = (lseek_file(fd, root_offset + (0x20 * i), 32)).to_bytes(32, byteorder='little')
        if "%02X" % record[0xb] == '20':
            size, next_cl, name = record[0x1c], record[0x1a], ("%s.%s" % (record[0:8].decode("utf-8"), record[8:11].decode("utf-8"))) if record[8:11].decode("utf-8") != "   " else ("%s" % (record[0:8].decode("utf-8")))
            f_name_list.append('files/'+name)
            print(" attribute: %02X\n" % record[0xb], 
                  "size:      %08X\n" % size, 
                  "cluster:   %02X\n" % next_cl,
                  "name:      %s\n"   % name) # root_offset + (list_count * 0x20) + sector_size * cluster_count + (next_cl - 3) * sector_size * cluster_count
            with open('files/'+name, 'wb') as f: None
            with open('files/'+name, 'ab') as f:
                while ("%03X" % next_cl) != "FFF":
                    data = lseek_file(fd, root_offset + (list_count * 0x20) + sector_size * cluster_count + (next_cl - 3) * sector_size * cluster_count, 
                                      sector_size * cluster_count if size > sector_size * cluster_count else size).to_bytes(sector_size * cluster_count if size > sector_size * cluster_count else size, 
                                                                                                                            byteorder='little')
                    size -= sector_size * cluster_count if size > sector_size * cluster_count else size
                    f.write(data)
                    next_cl = next_cluster(fd, fat_offset, next_cl)
    with open('files/sum', 'wb') as f:
        for fname in f_name_list:
            with open(fname, 'rb') as f2:
                data = f2.read()
            f.write(data)
    print(hashlib.md5(file_as_bytes(open('files/sum', 'rb'))).hexdigest())

def lseek_file(fd, address, size, byteorder='little'):
    try:
        os.lseek(fd, address, os.SEEK_SET)
        return int.from_bytes(os.read(fd, size), byteorder=byteorder)
    except Exception as error: print(error)

sector_size   = lseek_file(fd, 0xb,  2)
res_count     = lseek_file(fd, 0x0e, 2)
fat_count     = lseek_file(fd, 0x10, 1)
fat_size      = lseek_file(fd, 0x16, 2)
list_count    = lseek_file(fd, 0x0e, 2)
record_count  = lseek_file(fd, 0x12, 2)
cluster_count = lseek_file(fd, 0xd,  1)
fat_offset    = res_count * sector_size
root_offset   = fat_offset + (fat_count * fat_size * sector_size)
data_offset   = root_offset + (record_count * 32)
print("sector size 0x%04X" % (sector_size))
print("start  FAT  0x%04X" % (fat_offset))
print("start  root 0x%04X" % (root_offset))
print("start  data 0x%04X" % (data_offset))
for_root(fd, root_offset, list_count, cluster_count, sector_size, fat_offset, data_offset)

os.close(fd)