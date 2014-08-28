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
  int i=2;

  setresuid(0,0,0);

  check_existence(LXC_CREATE,1);
  check_existence(LXC_DESTROY,1);
  check_existence(LXC_START,1);
  check_existence(LXC_STOP,1);
  check_existence(LXC_ATTACH,1);

  if (argc < 3) {
    fprintf(stderr,"usage: chelper lxc lxc_command parameters\n");
    exit(1);
  }

  if (strcmp(argv[2],"lxc-create") == 0) {
    exit (lxc_create());
  }
  
  if (strcmp(argv[2],"lxc-destroy") == 0) {
    exit (lxc_destroy(1));
  }
  if (strcmp(argv[2],"lxc-stop") == 0) {
    exit (lxc_stop());
  }
  if (strcmp(argv[2],"lxc-start") == 0) {
    exit (lxc_start());
  }
  if (strcmp(argv[2],"lxc-attach") == 0) {
    if (argc < 4) {
      fprintf(stderr, "usage: chelper lxc lxc-attach wait|nowait command\n");
      exit(1);
    }
    exit(lxc_attach(argc,argv));
  }

  fprintf(stderr,"unrecognised lxc command\n");
  exit(42);
}

/* creates and starts the container */
int lxc_create() {

  int result=0;
  pid_t pid;
  int devnull;
  
  char *arg1[] = {LXC_CREATE,"-t", "ubuntu", "-n", LXC_NAME,"--","-u",LXC_USER, NULL};
  char *arg2[] = {LXC_START,"-d", "-n", LXC_NAME, NULL};

  pid = fork();
  if (pid == -1) {
    perror(PNAME);
    exit(1);
  }
  if (pid == 0) {
    /* 
       No output required or wanted
    */
    devnull = open("/dev/null", O_RDWR);
    if (devnull == -1) {
      perror(PNAME);
      exit(1);
    }
    dup2(devnull,1);
    dup2(devnull,2);
    close(devnull);

    if (execv(LXC_CREATE, arg1) == -1) {
      perror(PNAME);
      exit(1);
    }
    /* This is never reached */
  }
  else {
    wait (&result);
  }	 
  if (result != 0) {
    fprintf(stderr,"container creation failed\n");
    exit(1);
  }

  /* start if successful */
  pid = fork();
  if (pid == -1) {
    perror(PNAME);
    exit(1);
  }
  if (pid == 0) {
    /* 
       No output required or wanted
    */
    close(STDERR_FILENO);
    close(STDOUT_FILENO);
    if (execv(LXC_START, arg2) == -1) {
      perror(PNAME);
      exit(1);
    }
    /* This is never reached */
  }
  else {
    wait (&result);
  }	 
  if (result != 0) {
    fprintf(stderr,"container startup failed\n");
    exit(1);
  }

  exit(0);
}

int lxc_destroy(int reaction) {
  int result=0;
  pid_t pid;
  int devnull;
  
  char *arg1[] = {LXC_DESTROY,"-f", "-n", LXC_NAME, NULL};


  pid = fork();
  if (pid == -1) {
    perror(PNAME);
    exit(1);
  }
  if (pid == 0) {
    /* 
       No output required or wanted
    */
    devnull = open("/dev/null", O_RDWR);
    if (devnull == -1) {
      perror(PNAME);
      exit(1);
    }
    dup2(devnull,1);
    dup2(devnull,2);
    close(devnull);

    if (execv(LXC_DESTROY, arg1) == -1) {
      perror(PNAME);
      exit(1);
    }
    /* This is never reached */
  }
  else {
    wait (&result);
  }	 
  if ((result != 0) && (reaction == 0)) {
    fprintf(stderr,"container deletion failed\n");
    exit(1);
  }
  exit(0);
}


int lxc_stop() {
  int result=0;
  pid_t pid;
  int devnull;
  
  char *arg1[] = {LXC_STOP, "-n", LXC_NAME, NULL};


  pid = fork();
  if (pid == -1) {
    perror(PNAME);
    exit(1);
  }
  if (pid == 0) {
    /* 
       No output required or wanted
    */
    devnull = open("/dev/null", O_RDWR);
    if (devnull == -1) {
      perror(PNAME);
      exit(1);
    }
    dup2(devnull,1);
    dup2(devnull,2);
    close(devnull);

    if (execv(LXC_STOP, arg1) == -1) {
      perror(PNAME);
      exit(1);
    }
    /* This is never reached */
  }
  else {
    wait (&result);
  }	 
  exit(0);
}

int lxc_start() {
  int result=0;
  pid_t pid;
  int devnull;
  
  char *arg1[] = {LXC_START, "-n", LXC_NAME, "-d", NULL};


  pid = fork();
  if (pid == -1) {
    perror(PNAME);
    exit(1);
  }
  if (pid == 0) {
    /* 
       No output required or wanted
    */
    devnull = open("/dev/null", O_RDWR);
    if (devnull == -1) {
      perror(PNAME);
      exit(1);
    }
    dup2(devnull,1);
    dup2(devnull,2);
    close(devnull);

    if (execv(LXC_START, arg1) == -1) {
      perror(PNAME);
      exit(1);
    }
    /* This is never reached */
  }
  else {
    wait (&result);
  }	 
  exit(0);
}

/* lxc_attach(flag, argc,argv)
   flag 0: do not wait for completion
   flag 1: do wait for completion */

int lxc_attach(int argc, char **argv) {
  int result=0,i,flag=-1;
  pid_t pid,newpid;
  int devnull;
  char **arg1;

  if (strcmp(argv[3],"wait") == 0)
    flag = 1;
  if (strcmp(argv[3],"nowait") == 0)
    flag = 0;
  if (flag == -1) {
    fprintf(stderr,"you must define wait/nowait\n");
    exit(1);
  }

  arg1 = malloc(sizeof(char*) * (argc+1));
  arg1[0] = LXC_ATTACH;
  arg1[1] = "-n";
  arg1[2] = LXC_NAME;
  arg1[3] = "--";
    
  for (i=4;i < argc;i++) {
    arg1[i] = argv[i];
  }
  arg1[argc+1] = NULL;

  
  devnull = open("/dev/null", O_RDWR);
  if (devnull == -1) {
    perror(PNAME);
    exit(1);
  }

  dup2(devnull,1);
  dup2(devnull,2);

  close(devnull);

  pid = fork();
  if (pid == -1) {
    perror(PNAME);
    exit(1);
  }
  if (pid == 0) {
    if (flag == 0) {
      newpid = setsid();
    }

    if (execv(LXC_ATTACH, arg1) == -1) {
      perror(PNAME);
      exit(1);
    }
  }
  else {
    if (flag == 1)
      wait (&result);
  }	 
  exit(0);
}  
