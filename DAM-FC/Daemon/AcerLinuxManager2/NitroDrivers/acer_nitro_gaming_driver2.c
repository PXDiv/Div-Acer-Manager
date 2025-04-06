#include "acer_nitro_gaming_driver2.h"
#include "linux/fs.h"
#include "linux/init.h"
#include "linux/kdev_t.h"
#include "linux/kern_levels.h"
#include "linux/kstrtox.h"
#include "linux/printk.h"
#include "linux/wmi.h"
#include "linux/slab.h"  // Add explicit include for kmalloc

/* Define constants for magic numbers */
MODULE_LICENSE("GPL");
MODULE_AUTHOR("Div with Claude");
MODULE_DESCRIPTION("Acer Nitro Gaming Functions WMI Driver");
MODULE_VERSION("1.21");

static int cmajor = 0;
static struct class *cclass = NULL;
dev_t cdev;

static struct file_operations cfops = {
    .owner = THIS_MODULE,
    .write = cdev_user_write,
    .open = chdev_open,
    .release = chdev_release
};

struct chdev_data {
    struct cdev cdev;
};

static struct chdev_data cdev_data[2];

extern int chdev_uevent(const struct device *dev, struct kobj_uevent_env *env) {
    int ret;
    
    ret = add_uevent_var(env, "DEVMODE=%#o", 0666);
    if (ret)
        return ret;
        
    return 0;
}

void cdev_create(char *name, int major, int minor, struct class *class) {
    int ret;
    
    cdev_init(&cdev_data[minor].cdev, &cfops);
    cdev_data[minor].cdev.owner = THIS_MODULE;
    
    ret = cdev_add(&cdev_data[minor].cdev, MKDEV(major, minor), 1);
    if (ret < 0) {
        pr_err("Failed to add cdev for %s\n", name);
        return;
    }
    
    if (!device_create(class, NULL, MKDEV(major, minor), NULL, name)) {
        pr_err("Failed to create device for %s\n", name);
        cdev_del(&cdev_data[minor].cdev);
    }
}

ssize_t cdev_user_write(struct file *file, const char __user *buff, size_t count, loff_t *offset) {
    int cdev_minor = MINOR(file->f_path.dentry->d_inode->i_rdev);
    char *kbfr;
    int ispeed = 0;
    int ret;
    size_t safe_count;
    
    pr_info("Writing to: %d", cdev_minor);
    
    /* Limit buffer size to prevent excessive allocations */
    safe_count = min_t(size_t, count, 20);
    
    kbfr = kmalloc(safe_count + 1, GFP_KERNEL);
    if (kbfr == NULL)
        return -ENOMEM;
        
    if (copy_from_user(kbfr, buff, safe_count)) {
        ret = -EFAULT;
        goto out_free;
    }
    
    /* Ensure null termination */
    kbfr[safe_count] = '\0';
    
    pr_info("%s", kbfr);
    
    ret = kstrtoint(kbfr, 10, &ispeed);
    if (ret) {
        ret = -EINVAL;
        goto out_free;
    }
    
    switch (cdev_minor) {
        case 0:
            pr_info("CPUFAN");
            fan_set_speed(ispeed, FAN_CPU);
            break;
        case 1:
            pr_info("GPUFAN");
            fan_set_speed(ispeed, FAN_GPU);
            break;
        default:
            ret = -EINVAL;
            goto out_free;
    }
    
    ret = count;  /* Return original count to avoid confusing userspace */
    
out_free:
    kfree(kbfr);
    return ret;
}

extern int chdev_open(struct inode *inode, struct file *file) {
    try_module_get(THIS_MODULE);
    return 0;
}

extern int chdev_release(struct inode *inode, struct file *file) {
    module_put(THIS_MODULE);
    return 0;
}

/* WMI Driver Definition */
static struct wmi_device *w_dev;

struct driver_data_t {};

static const struct wmi_device_id w_dev_id[] = {
    {
        .guid_string = WMI_GAMING_GUID
    },
    {} /* Null terminated */
};

static struct wmi_driver wdrv = {
    .driver = {
        .owner = THIS_MODULE,
        .name = DRV_NAME,
        .probe_type = PROBE_PREFER_ASYNCHRONOUS
    },
    .id_table = w_dev_id,
    .remove = wmi_remove,
    .probe = wmi_probe,
};

void wmi_remove(struct wmi_device *w_devv) {
    w_dev = NULL;
    pr_info("Acer Nitro Gaming WMI device removed");
}

extern int wmi_probe(struct wmi_device *wdevv, const void *notuseful) {
    struct driver_data_t *driver_data;
    
    if (!wmi_has_guid(WMI_GAMING_GUID))
        return -ENODEV;
        
    driver_data = devm_kzalloc(&wdevv->dev, sizeof(struct driver_data_t), GFP_KERNEL);
    if (!driver_data)
        return -ENOMEM;
        
    dev_set_drvdata(&wdevv->dev, driver_data);
    w_dev = wdevv;
    
    /* Unlock the fan speeds */
    wmi_eval_int_method(METHOD_UNLOCK_FAN, UNLOCK_CODE1);
    wmi_eval_int_method(METHOD_UNLOCK_FAN, UNLOCK_CODE2);
    
    /* Set default fan speeds */
    wmi_eval_int_method(METHOD_SET_FAN, concatenate(DEFAULT_FAN_SPEED, FAN_CPU));
    wmi_eval_int_method(METHOD_SET_FAN, concatenate(DEFAULT_FAN_SPEED, FAN_GPU));
    
    /* Set default keyboard backlight - red */
    dy_kbbacklight_set(1, 5, 100, 1, 255, 0, 0);
    
    pr_info("Acer Nitro Gaming WMI device initialized");
    return 0;
}

/* WMI Functions */
extern void __wmi_eval_method(struct wmi_device *wdev, int methodid, int instance, struct acpi_buffer *inbuffer) {
    struct acpi_buffer out = {ACPI_ALLOCATE_BUFFER, NULL};
    acpi_status status;
    
    if (!wdev) {
        pr_err("WMI device not available");
        return;
    }
    
    status = wmidev_evaluate_method(wdev, instance, methodid, inbuffer, &out);
    if (ACPI_FAILURE(status))
        pr_err("WMI method %d failed: %s", methodid, acpi_format_exception(status));
        
    if (out.pointer)
        kfree(out.pointer);
}

extern void wmi_eval_method(int methodid, struct acpi_buffer inputacpi) {
    __wmi_eval_method(w_dev, methodid, 0, &inputacpi);
}

extern void wmi_eval_int_method(int methodid, int input) {
    struct acpi_buffer in = {(acpi_size)sizeof(input), &input};
    wmi_eval_method(methodid, in);
}

/* Concatenate Function */
unsigned concatenate(unsigned x, unsigned y) {
    unsigned pow = 10;
    while (y >= pow)
        pow *= 10;
    return x * pow + y;
}

/* Set Fan Speeds */
extern int fan_set_speed(int speed, int fan) {
    int merged = concatenate(speed, fan);
    pr_info("Setting fan %d to speed %d (merged: %d)", fan, speed, merged);
    wmi_eval_int_method(METHOD_SET_FAN, merged);
    return 0;
}

/* Keyboard RGB Led */
extern void dy_kbbacklight_set(int mode, int speed, int brg, int drc, int red, int green, int blue) {
    u8 dynarray[16] = {mode, speed, brg, 0, drc, red, green, blue, 0, 1, 0, 0, 0, 0, 0, 0};
    struct acpi_buffer in = {(acpi_size)sizeof(dynarray), dynarray};
    
    pr_info("Setting keyboard backlight: mode=%d, speed=%d, brightness=%d, rgb=(%d,%d,%d)",
            mode, speed, brg, red, green, blue);
    wmi_eval_method(METHOD_SET_KEYBOARD, in);
}

int module_startup(void) {
    int ret;
    
    if (!wmi_has_guid(WMI_GAMING_GUID)) {
        pr_err("Acer Nitro Gaming WMI GUID not found");
        return -ENODEV;
    }
    
    ret = alloc_chrdev_region(&cdev, 0, 2, "acernitrogaming");
    if (ret < 0) {
        pr_err("Failed to allocate character device region");
        return ret;
    }
    
    cmajor = MAJOR(cdev);
    
    cclass = class_create("acernitrogaming");
    if (IS_ERR(cclass)) {
        pr_err("Failed to create device class");
        ret = PTR_ERR(cclass);
        goto fail_class;
    }
    
    cclass->dev_uevent = chdev_uevent;
    cdev_create("fan1", cmajor, 0, cclass);
    cdev_create("fan2", cmajor, 1, cclass);
    
    ret = wmi_driver_register(&wdrv);
    if (ret) {
        pr_err("Failed to register WMI driver");
        goto fail_driver;
    }
    
    pr_info("Acer Nitro Gaming Functions WMI Driver Module loaded successfully");
    return 0;
    
fail_driver:
    device_destroy(cclass, MKDEV(cmajor, 0));
    device_destroy(cclass, MKDEV(cmajor, 1));
    class_destroy(cclass);
fail_class:
    unregister_chrdev_region(MKDEV(cmajor, 0), 2);
    return ret;
}

void module_finish(void) {
    pr_info("Acer Nitro Gaming Functions WMI Driver Module unloaded");
    device_destroy(cclass, MKDEV(cmajor, 0));
    device_destroy(cclass, MKDEV(cmajor, 1));
    class_destroy(cclass);
    unregister_chrdev_region(MKDEV(cmajor, 0), 2);
    wmi_driver_unregister(&wdrv);
}

module_init(module_startup);
module_exit(module_finish);
