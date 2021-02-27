python setup.py build_ext --inplace ## --embed
cython --embed -o knots.c knots.pyx

# GCC syntax description
# gcc <C_file_from_cython> -I<include_directory> -L<directory_containing_libpython> -l<name_of_libpython_without_lib_on_the_front> -o <output_file_name>

# Linux build
gcc -Os -fPIC ./knots.c -I/usr/include/python3.9 -L/usr/include/ -lpython3.9 -o knots

# Windows build
# gcc -Os -fPIC -D MS_WIN64 ./cython/knots.c -I/usr/include/python3.9 -L/usr/include/ -lpython3.9 -o knots