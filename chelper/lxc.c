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
#include <string.h>

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
    if (argc < 5) {
      fprintf(stderr, "usage: chelper lxc lxc-attach wait|nowait vocal|silent command\n");
      exit(1);
    }
    exit(lxc_attach(argc,argv));
  }
  if (strcmp(argv[2],"process_webdrive") == 0) 
    exit(process_webdriver());

  if (strcmp(argv[2],"copy_file") == 0) {
    if (argc < 3) {
      fprintf(stderr,"usage: chelper lxc copy_file srcfile");
      exit(1);
    }
    exit(copy_file(argv[3]));
  }

  fprintf(stderr,"unrecognised lxc command\n");
  exit(42);
}

/* creates and starts the container */
int lxc_create() {

  int result=0,counter=0;
  pid_t pid;
  int devnull;
  
  /*  char *arg1[] = {LXC_CREATE,"-t", "ubuntu", "-n", LXC_NAME,"--","-u",LXC_USER, "--packages", "firefox,python2.7,xvfb,python-pip", NULL}; */
  char *arg1[] = {LXC_CREATE,"-t", "ubuntu", "-n", LXC_NAME,"--","-u",LXC_USER, NULL};
  char *arg2[] = {LXC_START,"-d", "-n", LXC_NAME, NULL};
  char *arg3[] = {LXC_ATTACH, "-n", LXC_NAME, "--", "pip", "install", "-q", "-U", "--force-reinstall", "selenium", NULL};

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

  /* install selenium if successful */
  sleep(5);
  while (1==1) {
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
      if (execv(LXC_ATTACH, arg3) == -1) {
	perror(PNAME);
	exit(1);
      }
      /* This is never reached */
    }
    else {
      wait (&result);
    }	 
    if (result == 0) 
      break;
    counter++;
    if (counter < 10) {
      sleep(2);
      continue;
    }
    fprintf(stderr,"selenium install failed\n");
    exit(1);
  }

  /* Hack selenium to not delete cache and history */
  process_webdriver();
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
  int result=0,i,flag=-1,silentflag=-1;
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

  if (strcmp(argv[4],"silent") == 0)
    silentflag = 1;
  if (strcmp(argv[4],"vocal") == 0)
    silentflag = 0;
  if (silentflag == -1) {
    fprintf(stderr,"you must define silent/vocal");
    exit(1);
  }
  arg1 = malloc(sizeof(char*) * (argc+1));
  arg1[0] = LXC_ATTACH;
  arg1[1] = "-n";
  arg1[2] = LXC_NAME;
  arg1[3] = "--";
    
  for (i=5;i < argc;i++) {
    arg1[i-1] = argv[i];
  }
  arg1[argc] = NULL;

  if (silentflag == 1) {
    devnull = open("/dev/null", O_RDWR);
    if (devnull == -1) {
      perror(PNAME);
      exit(1);
    }

    dup2(devnull,1);
    dup2(devnull,2);
    
    close(devnull);
  }

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

int process_webdriver() {
  FILE *fp;
  long fsize;
  char *fco, *newfile, *c;
  int devnull, result;
  pid_t pid;

  fp = fopen(WEBDRIVER_REMOTE,"r");
  if (fp == NULL) {
    perror(PNAME);
    exit(1);
  }
  fseek(fp,0,SEEK_END);
  fsize = ftell(fp);
  fseek(fp,0,SEEK_SET);

  fco = malloc(sizeof(char)*(fsize+1));
  if (fco == NULL) {
    perror (PNAME);
    exit(1);
  }
  fread (fco, fsize, 1, fp);
  fclose(fp);
  fco[fsize] = 0;

  newfile = malloc(sizeof(char)*(fsize+120));
  if (newfile == NULL) {
    perror(PNAME);
    exit(1);
  }
  c = strstr(fco, "self.binary.kill()");
  if (c == NULL) {
    fprintf(stderr, "self.binary.kill() not found in webdriver\n");
    exit(1);
  }
  bzero(newfile, fsize+119);
  memcpy(newfile, fco, c-fco);
  strcat(newfile, "self.binary.kill()\n        return self.profile.path\n");
  strcat(newfile, c+18);

  fp = fopen(WEBDRIVER_REMOTE, "w");
  if (fp == NULL) {
    perror(PNAME);
    exit(1);
  }
  fputs(newfile, fp);
  fclose(fp);


  /* Compile to pyc */
  char *arg[] = {LXC_ATTACH, "-n", LXC_NAME, "--", PYTHON, "-m", "compileall", WEBDRIVER_LOCAL_DIR, NULL};
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

    if (execv(LXC_ATTACH, arg) == -1) {
      perror(PNAME);
      exit(1);
    }
    /* This is never reached */
  }
  else {
    wait (&result);
  }	 
  if (result != 0) {
    fprintf(stderr,"python compile failed\n");
    exit(1);
  }


  return(0);
}

int copy_file(char *src) {
  int f_in, f_out;
  char buf[1024];
  ssize_t nread;

  f_in = open(src, O_RDONLY);
  if (f_in < 0) {
    perror(PNAME);
    exit(1);
  }
  f_out = open(CONTAINER_TMP, O_WRONLY | O_CREAT | O_EXCL, 0777);
  if (f_out < 0) {
    perror(PNAME);
    exit(1);
  }

  while (nread = read(f_in, buf, sizeof(buf)), nread > 0) {
      char *out_b = buf;
      ssize_t nwritten;

      do {
	nwritten = write(f_out, out_b, nread);
	if (nwritten >= 0) {
	  nread -= nwritten;
	  out_b += nwritten;
	} 
	else {
	  fprintf(stderr, "file copy error\n");
	  exit(1);
	}
      } while (nread > 0);
    }
    close(f_in);
    close(f_out);
    return(0);
}            
