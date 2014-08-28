#include <stdio.h>
#define _GNU_SOURCE
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <dirent.h>
#include <sys/mount.h>

#include "chelper.h"

int check_existence(char *path, int exitflag) {
  struct stat buf;
  int i;

  i = stat(path,&buf);
  if ((i != 0) && (exitflag == 1)) {
    fprintf(stderr, "%s does not exist\n", path);
    exit(1);
  }

  return(i);
}

int process_lxc(int argc, char **argv) {
  int i=0;

  check_existence(LXC_CREATE,1);
  check_existence(LXC_DESTROY,1);
  check_existence(LXC_START,1);
  check_existence(LXC_STOP,1);
  check_existence(LXC_ATTACH,1);


  exit(0);
}

  
  

