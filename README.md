OVA To AWS
======
Импорт OVA в Amazon Web Services
## Перед импортом

1) [Зарегестрироваться на AWS](https://aws.amazon.com/)
2) Выбрать регион (далее region_name)(вкладка слева от username)
3) Перейти в `Security credentials`
4) Создать `Access key ID, Secret access key`
5) В папку со скриптом положить импортируемый образ

## Установка модулей (linux, ubuntu)

```bash
pip3 install -r requirements.txt
```

## Перед запуском

```bash
red@cadets:~/$ aws configure
```
Ввести: Access key ID,
        Secret access key,
        region_name,
        format_output **(обязательно json)**

## Использование

```bash
red@cadets:~/$ python3 import-image-to-ec2-aws.py -h
usage: import-image-to-ec2-aws.py [-h] [--access_key ACCESS_KEY] [--secret_key SECRET_KEY] [--region_name REGION_NAME] 
                                  [--vm_filename VM_FILENAME] [--bucket_name BUCKET_NAME] [--instance_type INSTANCE_TYPE]

optional arguments:
  -h, --help            show this help message and exit
  --access_key ACCESS_KEY
                        Enter your AWS Access Key
  --secret_key SECRET_KEY
                        Enter your AWS Secret Key
  --region_name REGION_NAME
                        Enter your AWS S3 Region
  --vm_filename VM_FILENAME
                        Enter your NSG file name
  --bucket_name BUCKET_NAME
                        Enter your AWS S3 Bucket Name
  --instance_type INSTANCE_TYPE
                        Enter your AWS Instance type
```

## Пример запуска скрипта

```bash
red@cadets:~/$ python3 import-image-to-ec2-aws.py --access_key AKIA4Q7UYUYNQ5QPDHHP --secret_key rUBvG467fxoiTwZvwgp8bb6mKRcSfr3YuYWdhsgQ --region_name eu-west-3 --vm_filename teamvm.ova --instance_type t2.micro
```
## Примечание

`instance_type` можно посмореть на [сайте](https://aws.amazon.com/ec2/instance-types/)
(`t2.micro` является бесплатным, но и производительность посредственная)
