#ifndef ACER_NITRO_GAMING_DRIVER2_H
#define ACER_NITRO_GAMING_DRIVER2_H
#include "linux/kobject.h"
#define DRV_NAME "acernitrogaming"
#define WMI_GAMING_GUID "7A4DDFE7-5B5D-40B4-8595-4408E0CC7F56"
#include <linux/init.h>
#include <linux/module.h>
#include <linux/version.h>
#include <linux/wmi.h>
#include <linux/acpi.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include "linux/device/class.h"
unsigned concatenate(unsigned, unsigned);
extern int fan_set_speed(int,int);
extern void __wmi_eval_method(struct wmi_device * ,int ,int ,struct acpi_buffer * );
extern void wmi_eval_method(int,struct acpi_buffer);
extern void wmi_eval_int_method(int,int);
extern void wmi_remove(struct wmi_device *);
extern int wmi_probe(struct wmi_device *, const void *);
extern ssize_t cdev_user_write(struct file *,const char __user *, size_t , loff_t *);
extern int chdev_uevent(const struct device*,struct kobj_uevent_env*);
extern void cdev_create(char *name, int major, int minor ,struct class*);
extern int chdev_open(struct inode *,struct file * );
extern int chdev_release(struct inode *,struct file *);
extern void dy_kbbacklight_set(int , int , int , int , int , int , int );
extern int module_startup(void);
extern void module_finish(void);
#endif
