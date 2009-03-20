/* Author: cocobear.cn@gmail.com
 * Using GPL v2
 */

#include <stdio.h>
#include <sys/types.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <string.h>
#include <arpa/inet.h>
#include <zlib.h>
#include <Python.h>

static PyObject * lookup(PyObject *self, PyObject *args)
{
    int fd;
    char *file_prefix;
    long file_size;
    long wc;
    char *word;

    char *data;
    const char *p;
    long index_size;
    int offset;
    int size;
    int flag = 0;
    unsigned char *buf;

    if (!PyArg_ParseTuple(args, "slls:lookup",
                &file_prefix, &file_size, &wc, &word)) {
        return NULL;
    }
    char idx_file_name[256];
    char dict_file_name[256];
    char gz_file_name[256];
    strcpy(idx_file_name, file_prefix);
    strcat(idx_file_name, ".idx");

    strcpy(dict_file_name, file_prefix);
    strcat(dict_file_name, ".dict");

    strcpy(gz_file_name, file_prefix);
    strcat(gz_file_name, ".dict.dz");
    if ((fd = open(idx_file_name, O_RDONLY)) < 0) {
        printf("open failed\n");
        return NULL;
    }
    data = (char *)mmap( NULL, file_size, PROT_READ, MAP_SHARED, fd, 0);
    p = data;
    int i;
    for (i=0;i<wc;i++) {
        index_size = strlen(p) + 1 + 2*sizeof(int);
        if (strcmp(word, p) == 0) {
            flag = 1;
        }
        if (flag == 1) {
            close(fd);
            offset = ntohl(*(int *)(p + strlen(p) + 1));
            size   = ntohl(*(int *)(p + strlen(p) + 1 + sizeof(int)));
            //printf("offset=%d\nsize\%d\n",offset,size);
            gzFile zfile;
            zfile = gzopen(gz_file_name, "rb");
            if (zfile == Z_NULL) {
                goto n;
            }
            gzseek(zfile, offset, SEEK_SET);
            buf = (unsigned char *)malloc(size+1);
            memset(buf, '\0', size+1);
            gzread(zfile, buf, size);
            //printf("%s\n", buf);
            return Py_BuildValue("s", buf);
n:
            if ((fd = open(dict_file_name, O_RDONLY)) < 0) {
                //printf("open %s failed \n",dict_file_name);
                return Py_BuildValue("s","Open dict file faile");
            }
            lseek(fd, offset, SEEK_SET);
            buf = (unsigned char *)malloc(size+1);
            memset(buf, '\0', size+1);
            read(fd, buf, size);
            //printf("%s\n",buf);
            close(fd);
            return Py_BuildValue("s", buf);
        }
        p += index_size;
    }

    return Py_BuildValue("s","Not found");
}

static struct PyMethodDef lookup_methods[] = {
    {"lookup", lookup, 1, "lookup(file_prefix, file_size, wc, word)"},
    {NULL, NULL}
};

void initlookup()
{
    (void) Py_InitModule("lookup", lookup_methods);
}
