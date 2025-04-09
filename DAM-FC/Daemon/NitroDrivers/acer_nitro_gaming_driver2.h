#ifndef ACER_NITRO_GAMING_DRIVER2_H
#define ACER_NITRO_GAMING_DRIVER2_H

/* Standard Linux kernel includes */
#include <linux/init.h>
#include <linux/module.h>
#include <linux/version.h>
#include <linux/wmi.h>
#include <linux/acpi.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/kobject.h>
#include <linux/device/class.h>
#include <linux/slab.h>  /* For kmalloc, kfree */

/* Driver constants */
#define DRV_NAME "acernitrogaming"
#define WMI_GAMING_GUID "7A4DDFE7-5B5D-40B4-8595-4408E0CC7F56"

/* Fan constants */
#define FAN_CPU 1
#define FAN_GPU 4
#define METHOD_UNLOCK_FAN 14
#define METHOD_SET_FAN 16
#define METHOD_SET_KEYBOARD 20
#define UNLOCK_CODE1 7681
#define UNLOCK_CODE2 1638410
#define DEFAULT_FAN_SPEED 512

/* Function prototypes with improved documentation */

/**
 * concatenate - Concatenate two unsigned integers
 * @x: First integer
 * @y: Second integer
 *
 * Returns: Concatenated result of x and y
 */
unsigned concatenate(unsigned x, unsigned y);

/**
 * fan_set_speed - Set the fan speed
 * @speed: Speed value
 * @fan: Fan ID (FAN_CPU or FAN_GPU)
 *
 * Returns: 0 on success, negative error code on failure
 */
extern int fan_set_speed(int speed, int fan);

/**
 * __wmi_eval_method - Evaluate WMI method with buffer
 * @wdev: WMI device
 * @methodid: Method ID
 * @instance: Instance ID
 * @inbuffer: Input buffer
 */
extern void __wmi_eval_method(struct wmi_device *wdev, int methodid, int instance, struct acpi_buffer *inbuffer);

/**
 * wmi_eval_method - Wrapper to evaluate WMI method
 * @methodid: Method ID
 * @inputacpi: Input ACPI buffer
 */
extern void wmi_eval_method(int methodid, struct acpi_buffer inputacpi);

/**
 * wmi_eval_int_method - Evaluate WMI method with integer parameter
 * @methodid: Method ID
 * @input: Integer input value
 */
extern void wmi_eval_int_method(int methodid, int input);

/**
 * wmi_remove - WMI device removal callback
 * @w_dev: WMI device being removed
 */
extern void wmi_remove(struct wmi_device *w_dev);

/**
 * wmi_probe - WMI device probe callback
 * @wdev: WMI device being probed
 * @notuseful: Unused parameter
 *
 * Returns: 0 on success, negative error code on failure
 */
extern int wmi_probe(struct wmi_device *wdev, const void *notuseful);

/**
 * cdev_user_write - Character device write callback
 * @file: File pointer
 * @buff: User buffer
 * @count: Buffer size
 * @offset: File offset
 *
 * Returns: Number of bytes written or negative error code
 */
extern ssize_t cdev_user_write(struct file *file, const char __user *buff, size_t count, loff_t *offset);

/**
 * chdev_uevent - Character device uevent callback
 * @dev: Device pointer
 * @env: Uevent environment
 *
 * Returns: 0 on success, negative error code on failure
 */
extern int chdev_uevent(const struct device *dev, struct kobj_uevent_env *env);

/**
 * cdev_create - Create character device
 * @name: Device name
 * @major: Major device number
 * @minor: Minor device number
 * @class: Device class
 */
extern void cdev_create(char *name, int major, int minor, struct class *class);

/**
 * chdev_open - Character device open callback
 * @inode: Inode pointer
 * @file: File pointer
 *
 * Returns: 0 on success, negative error code on failure
 */
extern int chdev_open(struct inode *inode, struct file *file);

/**
 * chdev_release - Character device release callback
 * @inode: Inode pointer
 * @file: File pointer
 *
 * Returns: 0 on success, negative error code on failure
 */
extern int chdev_release(struct inode *inode, struct file *file);

/**
 * dy_kbbacklight_set - Set keyboard backlight
 * @mode: Backlight mode
 * @speed: Animation speed
 * @brg: Brightness
 * @drc: Direction
 * @red: Red color component (0-255)
 * @green: Green color component (0-255)
 * @blue: Blue color component (0-255)
 */
extern void dy_kbbacklight_set(int mode, int speed, int brg, int drc, int red, int green, int blue);

/**
 * module_startup - Module initialization function
 *
 * Returns: 0 on success, negative error code on failure
 */
extern int module_startup(void);

/**
 * module_finish - Module cleanup function
 */
extern void module_finish(void);

#endif /* ACER_NITRO_GAMING_DRIVER2_H */
