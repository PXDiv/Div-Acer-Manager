#include "acer_nitro_gaming_driver2.h"
#include "linux/fs.h"
#include "linux/init.h"
#include "linux/kdev_t.h"
#include "linux/kern_levels.h"
#include "linux/kstrtox.h"
#include "linux/printk.h"
#include "linux/wmi.h"




MODULE_LICENSE("GPL");
static int cmajor= 0;

static struct class *cclass=NULL;
dev_t cdev;
static const struct file_operations cfops={
    .owner=THIS_MODULE,
    .write= cdev_user_write,
    .open= chdev_open,
    .release= chdev_release

};
struct chdev_data{
    struct cdev cdev;
};
static struct chdev_data cdev_data[2];
extern int chdev_uevent(const struct device *dev,struct kobj_uevent_env *env){
    add_uevent_var(env, "DEVMODE=%#o",0666);
    return 0;
}

void cdev_create(char * name, int major, int minor,  struct class *class){
    cdev_init(&cdev_data[minor].cdev,&cfops);
    cdev_data[minor].cdev.owner = THIS_MODULE;
    cdev_add(&cdev_data[minor].cdev,MKDEV(major,minor),1);
    device_create(class,NULL,MKDEV(major,minor),NULL,name);
}
ssize_t cdev_user_write(struct file * file,const char __user * buff, size_t count, loff_t *offset){
    int cdev_minor = MINOR(file->f_path.dentry->d_inode->i_rdev);
    printk(KERN_INFO"writing to : %d",cdev_minor);
    char * kbfr=kmalloc(count,GFP_KERNEL);
    int ispeed =0;
    if(kbfr==NULL)       // Check before copy
        return -ENOMEM;
    copy_from_user(kbfr,buff,count);
    int ix = strnlen(kbfr, count);
    if (ix > 0)          // check for 0
        kbfr[ix-1] = '\0';   // always terminate
    printk(KERN_INFO"%s",kbfr);
    switch(cdev_minor){
        case 0:
            printk(KERN_INFO"CPUFAN");
            kstrtoint(kbfr,10 ,&ispeed );
            fan_set_speed(ispeed,1 );
            break;
        case 1:
            printk(KERN_INFO"GPUFAN");
            kstrtoint(kbfr,10 ,&ispeed );
            fan_set_speed(ispeed,4 );
            break;
    }
    return count;
}
extern int chdev_open(struct inode * inode,struct file * file){
    try_module_get(THIS_MODULE);
    return 0;
}

extern int chdev_release(struct inode * inode,struct file * file){
    module_put(THIS_MODULE);
    return 0;
}
//Wmi Driver Definition
static struct wmi_device *w_dev ;

struct driver_data_t{};

static const struct wmi_device_id w_dev_id[] = {{
    .guid_string = WMI_GAMING_GUID
},
};

static struct wmi_driver wdrv = {
    .driver = {.owner = THIS_MODULE, .name = DRV_NAME, .probe_type=PROBE_PREFER_ASYNCHRONOUS},
    .id_table = w_dev_id,
    .remove = wmi_remove,
    .probe = wmi_probe,

};
void wmi_remove(struct wmi_device *w_devv) { w_dev = NULL; }

extern int wmi_probe(struct wmi_device *wdevv, const void *notuseful) {
    struct driver_data_t *driver_data;
    if(!wmi_has_guid(WMI_GAMING_GUID))
        return -ENOMEM;
    driver_data =
        devm_kzalloc(&wdevv->dev, sizeof(struct driver_data_t), GFP_KERNEL);
    dev_set_drvdata(&wdevv->dev,driver_data );
    w_dev = wdevv;
    //Unlock the fan speeds
    wmi_eval_int_method(14,7681 );
    wmi_eval_int_method(14,1638410 );
    //Set fan speeds to 512
    wmi_eval_int_method(16,5121 );
    wmi_eval_int_method(16,5124 );
    dy_kbbacklight_set(1, 5, 100, 1, 255, 0, 0);
    return 0;
}
//Wmi Functions
extern void __wmi_eval_method(struct wmi_device * wdev,int methodid ,int instance ,struct acpi_buffer *inbuffer){
    struct acpi_buffer out = {ACPI_ALLOCATE_BUFFER, NULL};
    wmidev_evaluate_method(wdev,instance ,methodid ,inbuffer ,&out );
}
extern void wmi_eval_method(int methodid,struct acpi_buffer inputacpi){
    __wmi_eval_method(w_dev,methodid ,0 ,&inputacpi );
}
extern void wmi_eval_int_method(int methodid,int input){
    struct acpi_buffer in = {(acpi_size)sizeof(input),&input};
    wmi_eval_method(methodid,in );
}
//Concatenate Function*
//Thanks to: https://stackoverflow.com/questions/12700497/how-to-concatenate-two-integers-in-c

unsigned concatenate(unsigned x, unsigned y) {
    unsigned pow = 10;
    while(y >= pow)
        pow *= 10;
    return x * pow + y;
}
//Set Fan Speeds

extern int fan_set_speed(int speed ,int fan ){
    int merged=  concatenate(speed,fan);
    printk(KERN_INFO"%d",merged);
    wmi_eval_int_method(16,merged );
    return 0;
}
//Keyboard RGB Led
extern void dy_kbbacklight_set(int mode, int speed, int brg, int drc, int red, int green, int blue){
    u8 dynarray [16] = {mode, speed, brg, 0, drc, red, green, blue, 0, 1, 0, 0, 0, 0, 0, 0};
    struct acpi_buffer in  = {(acpi_size)sizeof(dynarray),dynarray};
    wmi_eval_method(20,in);
}
int module_startup(void){
    if(!wmi_has_guid(WMI_GAMING_GUID))
        return -ENODEV;
    if(alloc_chrdev_region(&cdev,0 ,2 ,"acernitrogaming" )<0)
        return -ENXIO;
    cmajor = MAJOR(cdev);
    cclass = class_create("acernitrogaming");
    cclass->dev_uevent=chdev_uevent;
    cdev_create("fan1",cmajor ,0,cclass );
    cdev_create("fan2",cmajor ,1,cclass );
    wmi_driver_register(&wdrv);

    printk("Acer Nitro Gaming Functions Wmi Driver Module was loaded");
    return 0;
}
void module_finish(void){
    printk("Acer Nitro Gaming Functions Wmi Driver Module was unloaded");
    device_destroy(cclass, MKDEV(cmajor,0));
    device_destroy(cclass, MKDEV(cmajor,1));
    class_destroy(cclass);
    unregister_chrdev_region(MKDEV(cmajor,0 ),MINORMASK );
    wmi_driver_unregister(&wdrv);

}

module_init(module_startup);
module_exit(module_finish);
