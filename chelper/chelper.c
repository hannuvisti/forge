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



/* Detach image. Find device from /etc/mtab
   umount and delete loopback association.
   Lots of fork()ing here
*/

int detach_image(void) {
  pid_t pid;
  int counter = 0;
  int result,completed,outerloop, outercompleted;
  char *s,*device,*mountpoint;
  FILE *fp;
  char buf[1024];   /* just something big */

  outerloop = 0;
  outercompleted = 0;

  while (outerloop < 2) {
    completed = 0;
    fp = fopen("/etc/mtab", "r");
    if (fp == NULL) {
      perror(PNAME);
      exit(1);
    }
    while (fgets(buf,1023,fp) != NULL) {
      s = strstr(buf, MOUNTPOINT);
      if (!s)
	continue;
      if (strlen(s) < 10)     /*something fishy is going on */
	continue;
      else {
	completed=1;
	break;
      }
    }
    fclose(fp);

    if (!completed) {
      outerloop++;
      sleep(1);
      continue;
    }
    else 
      break;
  }
  if (!completed) {
    fprintf(stderr,"nothing mounted\n");
    return (-1);
  }

  device = strtok(buf," ");
  if (!device) {
    fprintf(stderr, "malformed mtab entry %s\n",buf);
    exit(1);
  }
  mountpoint = strtok(NULL," ");
  if (!mountpoint) {
    fprintf(stderr, "malformed mtab entry %s\n",buf);
    exit(1);
  }

  char *ara[] = {UMOUNT, mountpoint,NULL};
  while (1==1) {
    counter++;
    sync();
    sleep(1);
    pid = fork();
    if (pid == -1) {
      perror(PNAME);
      exit(1);
    }
    if (pid == 0) {
      /*
	Umount is not permitted for setuid processes. Setuid must be 
	camouflaged.
      */
      setresuid(0,0,0);
      if (execv(UMOUNT, ara) == -1) {
	fprintf(stderr, "this should not happen\n");
	exit(1);
      }
      /* Not reached */
      return (-1);
    }
    else {
      wait (&result);
      if (result == 0)
	break;
    }
    if (counter > 10) {
      fprintf(stderr, "mount point busy, cannot continue\n");
      exit(1);
    }
  }

  char *arl[] = {LOSETUP, "-d", device, NULL};
  counter = 0;
  while (1 == 1) {
    counter++;
    pid = fork();
    if (pid == -1) {
      perror(PNAME);
      exit(1);
    }
    if (pid == 0) {
      if (execv(LOSETUP, arl) == -1) {
	fprintf(stderr, "this should not happen\n");
	exit(1);
      }
      return (-1);
    }
    else {
      wait (&result);
      if (result == 0) 
	break;
    }
    if (counter > 10) {
      fprintf(stderr, "cannot detach loopback device %s\n", device);
      exit(1);
    }
    sync();
    sleep(1);
  }
  return (result);
}

int detach_device(char *device) {
  pid_t pid;
  int result;

  char *arg[] = {LOSETUP,"-d",device,NULL};
  pid = fork();
  if (pid == -1) {
    perror(PNAME);
    exit(1);
  }
  if (pid == 0) {
    if (execv(LOSETUP, arg) == -1) {
      fprintf(stderr, "this should not happen\n");
      exit(1);
    }

    return (-1);
  }
  else {
    wait (&result);
    return (result);
  }

  return(-1);
}


/* Parse "size" argument to either interpret it as a number or multiply with
   a constant based on kilo/mega/giga postfix */

long calculate_size(char *sc) {
  long q=0;
  char mchar=0;
  long multiplier = 1;

  if (strlen(sc) < 2) {
    fprintf(stderr, "size must be a numeric or m/k/g\n");
    exit(1);
  }

  mchar = sc[strlen(sc)-1];
  if (mchar == 'k' || mchar == 'K')
    multiplier = 1024;
  if (mchar == 'm' || mchar == 'M')
    multiplier = 1024*1024;
  if (mchar == 'g' || mchar == 'G')
    multiplier = 1024*1024*1024;

  q = atol(sc);
  q *= multiplier;
  
  if (q < 65535) {
    fprintf(stderr, "too short file %ld\n", q);
    exit(1);
  }

  return (q);
}

/* Make sure a path has only alphanumeric characters and maximum of 1 
   consecutive dot or slash. Dash is also permitted */

int sanitize_path(char *path) {
  int i=0, s=0, k=0;
  char c;

  for (i=0;i < strlen(path);i++) {
    c = path[i];
    if (isalnum(c) || c == '-') {
      s=0;
      k=0;
      continue;
    }
    if (c == '.' && s == 0) {
      s++;
      k=0;
      continue;
    }
    if (c == '/'&& k == 0) {
      k++;
      s=0;
      continue;
    }

    if (s == 1) {
      fprintf(stderr,".. in path, exiting\n");
      exit(1);
    }
    if (k == 1) {
      fprintf(stderr,"// in path, exiting\n");
      exit(1);
    }

    fprintf(stderr, "Illegal character %c in path, exiting\n",c);
    exit(1);
  }
  return (1);
}

/* Check if mount point is empty true=empty  false=not empty */
int is_dir_empty(char *path) {
  int c=0;
  struct dirent *dent=NULL;
  DIR *directory=NULL;

  directory = opendir(path);
  if (directory == NULL) {
    perror(PNAME);
    exit(1);
  }

  while ((dent = readdir(directory)) != NULL) 
    if (++c > 2)
      break;

  if (closedir(directory) == -1) {
    perror(PNAME);
    exit(1);
  }
  if (c <= 2)
    return 1;
  else
    return 0;
}

/* Mount a specific file system */
int mount_ntfs_filesystem(char *device) {
  int result;
  pid_t pid;

  if (!is_dir_empty(MOUNTPOINT)) {
    fprintf(stderr,"Mount point not empty\n");
    return (-1);
  }
  char *arg[] = {NTFS_3G, "-o", "windows_names,streams_interface=windows", device, MOUNTPOINT, NULL};
  
  pid = fork();
  if (pid == -1) {
    perror(PNAME);
    exit(1);
  }
  if (pid == 0) {
    /* 
       Tuxera NTFS-3g does not work for a setuid process unless ntfs3g-binary
       is suid root as well. This is discouraged, so we camouflage the fact
       that the program is running setuid 
    */
    setresuid(0,0,0);
    if (execv(NTFS_3G, arg) == -1) {
      fprintf(stderr, "this should not happen\n");
      exit(1);
    }
    /* Not reached */
    return (-1);
  }
  else {
    wait (&result);
    return (result);
  }
  /* Not reached */

  return (-1);
}

/* Attach a file to a loopback interface. Return char* to loopback device name 
   After this function the rest of the program can assure the loopback device is 
   "owned" by this process 
   Also check that file attached is a regular file, not a symlink, device, 
   fifo or anything weird, and that hard link count is exactly 1.
*/

char *attach_file(char *prefix, char *command) {
  int i,result=42;
  char *path;
  pid_t   pid;
  char  *arg[10];
  int ipipe[2];
  char *loopback;
  struct stat statbuf;

  if (!is_dir_empty(MOUNTPOINT)) {
    fprintf(stderr,"Mount point not empty\n");
    exit(1);
  }
  path = malloc(sizeof(char)*(strlen(prefix)+strlen(command)));
  if (path == NULL) {
    perror(PNAME);
    exit(1);
  }
  strcpy(path, prefix);
  strcat(path, command);
  sanitize_path(path);

  if (lstat (path, &statbuf) == -1) {
    perror(PNAME);
    exit(1);
  }
  if (statbuf.st_nlink != 1) {
    fprintf(stderr, "File has hard links to it, cannot proceed.\n");
    exit(1);
  }
  if ((statbuf.st_mode & S_IFMT) != S_IFREG) {
    fprintf(stderr, "file is not a regular file, go away\n");
    exit(1);
  }



  /* A kludge to redirect child stdout back to parent to find a loopback device */
  if (pipe(ipipe)) {
    perror(PNAME);
    exit(1);
  }

  /* Fork to run losetup -f to get a free loopback interface */
  pid = fork();
  if (pid == -1) {
    perror(PNAME);
    exit(1);
  }
  if (pid == 0) {
    close(STDOUT_FILENO);
    close(STDERR_FILENO);

    dup2(ipipe[1], STDOUT_FILENO);
    close(ipipe[0]);
    close(ipipe[1]);

    arg[0] = LOSETUP;
    arg[1] = "-f";
    arg[2] = NULL;
    if (execv(LOSETUP, arg) == -1) {
      perror(PNAME);
      exit(1);
    }
    /* This is never reached */
    return NULL;
  }
  else {
    close(ipipe[1]);
    loopback = malloc(256*sizeof(char));
    if (loopback == NULL) {
      perror(PNAME);
      exit(1);
    }
    loopback[read(ipipe[0],loopback,256)] = 0;
    if (strlen(loopback) < 5) {
      fprintf(stderr, "no loopback device found\n");
      wait(&result);
      close(ipipe[0]);
      exit(1);
    }
    /* Get a free loopback device to loopback */
    loopback[strlen(loopback)-1] = 0;
    wait(&result);
    close(ipipe[0]);
    if (result != 0) {
      fprintf(stderr, "this should not happen, losetup -f did not return a proper value\n");
      exit(result);
    }
    /* Attach the loopback device. Examine return value as not a single state operation */
    arg[0] = LOSETUP;
    arg[1] = loopback;
    arg[2] = path;
    arg[3] = NULL;

    /* Fork to exec losetup /dev/loopx pathname */
    pid = fork();
    if (pid == -1) {
      perror(PNAME);
      exit(1);
    }
    if (pid == 0) {
      if (execv(LOSETUP, arg) == -1) {
	perror(PNAME);
	exit(1);
      }
      /* This is never reached */
      return NULL;
    }
    else {
      wait (&result);
      if (result == 0) 
	return loopback;
      else {
	free(loopback);
	return NULL;
      }
    }
  }
}
/* Creates a NTFS by executing mkfs.ntfs. This does not need root privileges */
int create_ntfs_filesystem(char *prefix, char *filename, char *partname, int cluster_size) {
  /*  char *arg[20];*/
  char *path;
  int i,result=0;
  char cluster_string[8];
  pid_t pid;
  
  if (setuid(getuid()) == -1) {
    perror(PNAME);
    exit(1);
  }

  if (filename == NULL) {
    fprintf(stderr, "filename unset\n");
    exit(1);
  }
  if (partname == NULL) {
    fprintf(stderr, "partition name unset\n");
    exit(1);
  }
  path = malloc(sizeof(char)*(strlen(prefix)+strlen(filename)));
  if (path == NULL) {
    perror(PNAME);
    exit(1);
  }
  strcpy(path, prefix);
  strcat(path, filename);
  sanitize_path(path);

  sprintf(cluster_string, "%d", cluster_size);
  
  char *arg[] = {MKFS_NTFS,"-L", partname, "-c", cluster_string, "-s", "512", "-p", "0", "-S", "0", "-H", "0", "-F", "-f", "-q", path, NULL};

  pid = fork();
  if (pid == -1) {
    perror(PNAME);
    exit(1);
  }
  if (pid == 0) {
    /* 
       mkfs complains about file not being a block device.
       We don't want that. 
    */
    close(STDERR_FILENO);
    close(STDOUT_FILENO);
    if (execv(MKFS_NTFS, arg) == -1) {
      perror(PNAME);
      exit(1);
    }
    /* This is never reached */
  }
  else {
    wait (&result);
    return (result);
  }	 
  /* This is never reached */
  return (-1);
}  

/* Creates a file of size X, either empty or random */

void create_file(char *prefix, char *filename, long size, int contents) {
  long i;
  char *path,wchar,*fbuf;
  int fd;

  /* This does not need root privileges */
  if (setuid(getuid()) == -1) {
    perror(PNAME);
    exit(1);
  }
  if (filename == NULL) {
    fprintf(stderr, "filename unset\n");
    exit(1);
  }

  path = malloc(sizeof(char)*(strlen(prefix)+strlen(filename)));
  if (path == NULL) {
    perror(PNAME);
    exit(1);
  }
  strcpy(path, prefix);
  strcat(path, filename);
  sanitize_path(path);

  fd = open(path,O_EXCL|O_CREAT|O_WRONLY, S_IRUSR|S_IWUSR| S_IRGRP|S_IWGRP|S_IROTH);


  /* Refuse to overwrite an existing file */

  if (fd == -1) {
    fprintf(stderr,"File exists\n");
    exit(1);
  }
  fbuf = malloc(sizeof(char)*(size+1));
  if (fbuf == NULL) {
    perror(PNAME);
    exit(1);
  }
  wchar = 0;
  for (i=0;i<size;i++) {
    if (contents == C_RANDOM) {
      wchar = rand() % 256;
    }
    fbuf[i] = wchar;

  }

  if (write(fd,fbuf,(size_t) size) == -1) {
    perror(PNAME);
    exit(1);
  }
  free (fbuf);
  close(fd);
}





main (int argc, char **argv) {
  char *params[10], *lodevice;
  char *prefix, *param, *mountpoint;
  pid_t pid, cluster_size=0;
  int status,opt=0,q=0;
  long size=0;

#ifdef PATH  
  if (strlen(PATH) > MAX_PATH_LENGTH) {
    fprintf(stderr, "too long PATH\n");
    exit(1);
  }
  prefix = malloc(sizeof(char)*strlen(PATH));
  if (prefix == NULL) {
    perror(PNAME);
    exit(1);
  }
  strcpy (prefix,PATH);
#else
#error "must define PATH"
#endif

#ifdef MOUNTPOINT
  if (strlen(MOUNTPOINT) > MAX_PATH_LENGTH) {
    fprintf(stderr, "too long MOUNTPOINT\n");
    exit(1);
  }
  mountpoint = malloc(sizeof(char)*strlen(MOUNTPOINT));
  if (mountpoint == NULL) {
    perror(PNAME);
    exit(1);
  }
  strcpy (mountpoint,MOUNTPOINT);
  sanitize_path(mountpoint);
#else
#error "must define MOUNTPOINT"
#endif

  if (argc < 2) {
    fprintf(stderr,"Usage: %s [create fstype size cluster_size name [clean | random] filename | attach fstype filename | detach]\n", PNAME);
    exit(1);
  }

  if (strcmp(argv[1], "create") == 0) {
    if (argc != 8) {
      fprintf(stderr,"Usage: %s create fstype size cluster_size name [clean | random] filename\n", PNAME);
      exit(1);
    }
    /* freopen("/dev/null","w",stderr);*/
    if (strlen(argv[3]) > 12) {
      fprintf(stderr,"Too long size parameter\n");
      exit(1);
    }
    size = calculate_size(argv[3]);
    if (strlen(argv[7]) > MAX_PATH_LENGTH) {
      fprintf(stderr, "Too long parameter %s\n", argv[7]);
      exit(1);
    }
    param = malloc(sizeof(char)*strlen(argv[7]));
    if (param == NULL) {
      perror(PNAME);
      exit(1);
    }
    strcpy(param, argv[7]);
    if ((atoi(argv[4]) < 1 || atoi (argv[4]) > 32) || atoi(argv[4]) & 1) {
      fprintf(stderr,"Cluster size must be a multiple of 2 and max 32\n");
      exit(1);
    }
    cluster_size = atoi(argv[4])*512;

    /* Generally we could be more allowing here but use the same routine
       for reasons of pure laziness. 
       Technically only white space, ?, *, " and ' should be really 
       frowned upon here 
    */
    sanitize_path(argv[5]);
    if (strlen(argv[5]) > 20) {
      fprintf(stderr, "too long parameter %s", argv[5]);
      exit(1);
    }
    if (strcmp(argv[6], "random") == 0) {
      create_file(prefix, param, size, C_RANDOM);
    } 
    else {
      create_file(prefix, param, size, C_ZERO);
    }
    if (strcmp(argv[2], "ntfs") == 0) {
      create_ntfs_filesystem(prefix, param, argv[5], cluster_size);
      exit(0);
    }
    else {
      fprintf(stderr, "Unknown file system type %s\n", argv[2]);
      exit(1);
    }
  }    


  
  /* Attach */
  if (strcmp(argv[1], "attach") == 0) {
    if (argc != 4) {
      fprintf(stderr,"Usage: %s attach fstype filename\n", PNAME);
      exit(1);
    }
    if (strlen(argv[3]) > MAX_PATH_LENGTH) {
      fprintf(stderr, "Too long parameter %s\n", argv[3]);
      exit(1);
    }
    param = malloc(sizeof(char)*strlen(argv[3]));
    if (param == NULL) {
      perror(PNAME);
      exit(1);
    }
    strcpy(param, argv[3]);
    lodevice = attach_file(prefix,param);
    if (lodevice) {
      if (strcmp(argv[2],"ntfs") == 0) {
	q = mount_ntfs_filesystem(lodevice);
	if (q != 0) 
	  detach_device(lodevice);
	exit(q);
      }
      else {
	fprintf(stderr, "unknown file system type %s\n", argv[2]);
	detach_device(lodevice);
	exit(1);
      }
    }
    else
      fprintf (stderr, "Cannot find loopback device\n");
    exit(0);
  }
  
  /* detach */
  if (strcmp(argv[1], "detach") == 0) {
    freopen("/dev/null","w",stderr);
    exit(detach_image());
  }
  fprintf(stderr,"Usage: %s [create fstype size cluster_size name [clean | random] filename | attach fstype filename | detach]\n", PNAME);  
  exit(1);
}

