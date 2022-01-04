#!/usr/bin/env python3

############################################# 
# Import required libraries
############################################# 
import pexpect, os, sys, time, argparse, json
import boto3
import cursor
import progressbar
from boto3.s3.transfer import S3Transfer
from colorama import init
from colorama import Fore, Back, Style


cursor.hide()
init()
############################################# 
# Start script
############################################# 
### start main function
def main():
   # add cli options (email, github, interval) 
   parser = argparse.ArgumentParser()
   parser.add_argument("--access_key", default="", type=str,
                     help="Enter your AWS Access Key")
   parser.add_argument("--secret_key", default="", type=str,
                     help="Enter your AWS Secret Key")
   parser.add_argument("--region_name", default="us-east-1", type=str,
                     help="Enter your AWS S3 Region")
   parser.add_argument("--vm_filename", default="", type=str,
                     help="Enter your NSG file name")
   parser.add_argument("--bucket_name", default="", type=str,
                     help="Enter your AWS S3 Bucket Name")
   parser.add_argument("--instance_type", default="", type=str,
                     help="Enter your AWS Instance type")
   args = parser.parse_args()
   #print(args)

   #save cli variables
   access_key = args.access_key                   
   secret_key = args.secret_key
   region_name = args.region_name
   vm_filename = args.vm_filename
   bucket_name = args.bucket_name
   instance_type = args.instance_type

   # # check aws is installed correctly 
   print(Fore.YELLOW +'[*]' + Fore.BLUE + ' Verify AWS installation', end="\r")

   output = pexpect.run('aws --version')
   if not b'aws-cli' in output:
      print('ERROR: AWS is not installed in this machine. Please install AWS-CLI.')
      print('      For information regarding this procedure, refer to the current AWS official documentation at: ')
      print('      http://docs.aws.amazon.com/cli/latest/userguide/installing.html#install-bundle-other-os')
      sys.exit()

   print(Fore.GREEN + ' ✔ ' + Fore.BLUE + ' Verify AWS installation')

   #check if enviroment variables are set correctly
   if not "LC_ALL" in os.environ:
      os.environ["LC_ALL"] = "en_US.UTF-8"

   print(Fore.YELLOW +'[*]' + Fore.BLUE + ' Create a trusted policy to be able to perform certain AWS operation', end="\r")

   file_trust_policy = open('trust-policy.json', 'w')
   s='''{
      "Version":"2012-10-17",
      "Statement":[
         {
            "Sid":"",
            "Effect":"Allow",
            "Principal":{
               "Service":"vmie.amazonaws.com"
            },
            "Action":"sts:AssumeRole",
            "Condition":{
               "StringEquals":{
                  "sts:ExternalId":"vmimport"
               }
            }
         }
      ]
   }'''
   file_trust_policy.write(s)
   file_trust_policy.close()
   print(Fore.GREEN + ' ✔ ' + Fore.BLUE + ' Create a trusted policy to be able to perform certain AWS operation')
   
   print(Fore.YELLOW +'[*]' + Fore.BLUE + ' Create a role named vmimport and give VM Import/Export access to it', end="\r")

   pexpect.run('aws iam create-role --role-name vmimport --assume-role-policy-document file://trust-policy.json')

   print(Fore.GREEN + ' ✔ ' + Fore.BLUE + ' Create a role named vmimport and give VM Import/Export access to it')

   print(Fore.YELLOW +'[*]' + Fore.BLUE + ' Connect to s3', end="\r")

   s3 = boto3.client('s3')
   
   print(Fore.GREEN + ' ✔ ' + Fore.BLUE + ' Connect to s3 success')

   if bucket_name == "":
      print(Fore.YELLOW +'[*]' + Fore.BLUE + ' Create bucket', end="\r")
      bucket_name = os.urandom(16).hex()
      bucket_name += "ctfbucket"

      bucket = s3.create_bucket(Bucket=bucket_name, 
                              CreateBucketConfiguration={'LocationConstraint': region_name}
                              )
      print(Fore.YELLOW + ' ☆ ' + Fore.BLUE + " Bucket name: " + Fore.YELLOW + "%s" % bucket_name)

   print(Fore.YELLOW +'[*]' + Fore.BLUE + ' Create a role policy to be able to perform certain AWS operation', end="\r")
   file_role_policy = open('role-policy.json', 'w')
   s='''{
      "Version":"2012-10-17",
      "Statement":[
         {
            "Effect":"Allow",
            "Action":[
               "s3:ListBucket",
               "s3:GetBucketLocation"
            ],
            "Resource":[
               "arn:aws:s3:::'''+bucket_name+'''"
            ]
         },
         {
            "Effect":"Allow",
            "Action":[
               "s3:GetObject"
            ],
            "Resource":[
               "arn:aws:s3:::'''+bucket_name+'''/*"
            ]
         },
         {
            "Effect":"Allow",
            "Action":[
               "ec2:ModifySnapshotAttribute",
               "ec2:CopySnapshot",
               "ec2:RegisterImage",
               "ec2:Describe*"
            ],
            "Resource":"*"
         }
      ]
   }'''
   file_role_policy.write(s)
   file_role_policy.close()
   print(Fore.GREEN + ' ✔ ' + Fore.BLUE + ' Create a role policy to be able to perform certain AWS operation')

   print(Fore.YELLOW +'[*]' + Fore.BLUE + ' Attach the policy to the role', end="\r")
   pexpect.run('aws iam put-role-policy --role-name vmimport --policy-name vmimport --policy-document file://role-policy.json')
   print(Fore.GREEN + ' ✔ ' + Fore.BLUE + ' Attach the policy to the role')

   print(Fore.YELLOW +'[*]' + Fore.BLUE + ' Create containers file, which contains information about the image', end="\r")
   file_containers = open('containers.json', 'w')
   s='''[{
      "Description": "VM-from-OVA",
      "Format": "ova",
      "UserBucket": {
         "S3Bucket": "'''+bucket_name+'''",
         "S3Key": "'''+vm_filename+'''"
      }
   }]'''
   file_containers.write(s)
   file_containers.close()
   print(Fore.GREEN + ' ✔ ' + Fore.BLUE + ' Create containers file, which contains information about the image')

   print(Fore.YELLOW +'[*]' + Fore.BLUE + ' Upload file', end="\r")
   transfer = S3Transfer(s3)
   statinfo = os.stat(vm_filename)
   up_progress = progressbar.progressbar.ProgressBar(maxval=statinfo.st_size)
   up_progress.start()
   
   def upload_progress(chunk):
      up_progress.update(up_progress.currval + chunk)

   transfer.upload_file(vm_filename, bucket_name, vm_filename, callback=upload_progress)
   up_progress.finish()

   print(Fore.GREEN + ' ✔ ' + Fore.BLUE + ' File Upload')

   print(Fore.YELLOW +'[*]' + Fore.BLUE + ' Connect to ec2', end="\r")
   ec2 = boto3.client( 'ec2',
                  aws_access_key_id=access_key,
                  aws_secret_access_key=secret_key,
                  region_name=region_name
                  ) 
   print(Fore.GREEN + ' ✔ ' + Fore.BLUE + ' Connect to ec2 success')

   print(Fore.YELLOW +'[*]' + Fore.BLUE + ' Create securityGroup', end="\r")
   group_name = os.urandom(16).hex()+"ctfsec"
   response = ec2.create_security_group(GroupName=group_name, Description='lolKekCheburek')
   security_group_id = response['GroupId']

   data = ec2.authorize_security_group_ingress(
      GroupId=security_group_id,
      IpPermissions=[
                  {'IpProtocol': 'tcp',
                     'FromPort': 0,
                     'ToPort': 65535,
                     'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                  {'IpProtocol': 'udp',
                     'FromPort': 0,
                     'ToPort': 65535,
                     'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                  {'IpProtocol': 'tcp',
                     'FromPort': 22,
                     'ToPort': 22,
                     'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
               ])
   print(Fore.YELLOW + ' ☆ ' + Fore.BLUE + " Security name: " + Fore.YELLOW + "%s" % group_name)

   print(Fore.YELLOW +'[*]' + Fore.BLUE + ' Execute the role policy', end="\r")
   output = pexpect.run('aws ec2 import-image --description "VM-from-OVA" --disk-containers file://containers.json').decode()
   image_id = ""
   try:
      s = json.loads(output)
      image_id = s['ImportTaskId']
   except:
      print(Fore.RED + ' ✘  error while dump json  ')
      exit(-1)

   print(Fore.YELLOW +'[*]' + Fore.BLUE + ' Remove the temp files (trust-policy.json, role-policy.json, containers.json)', end="\r")
   pexpect.run('rm trust-policy.json') 
   pexpect.run('rm role-policy.json') 
   pexpect.run('rm containers.json')
   print(Fore.GREEN + ' ✔ ' + Fore.BLUE + 'Remove the temp files (trust-policy.json, role-policy.json, containers.json)')

   print(Fore.YELLOW +'[➜ ]' + Fore.BLUE + ' Check the status of loading the OVA image ' + Fore.YELLOW + '%s' % image_id + Fore.BLUE + ' to your EC2. This usually takes 20-30 minutes')
   while not "success" in output:
      progress_output = pexpect.run('aws ec2 describe-import-image-tasks --import-task-ids %s' % image_id).decode()
      progress_start='Progress": "'
      
      if progress_start in progress_output:
         progress = (progress_output.split(progress_start))[1].split('"')[0]
         print(Fore.GREEN + '[⌚]' + Fore.BLUE + ' The progress on importing the image to EC2 is: ' + Fore.YELLOW + progress + '%', end = "\r")
   
      if "completed" in json.loads(progress_output)['ImportImageTasks'][0]['Status']:
         output = "success"
         s = json.loads(progress_output)
         image_id = s['ImportImageTasks'][0]['ImageId']

      time.sleep(120)
   
   print()
   print('╔═════════════════════════════════════════════════════════╗')
   print('║       Image has been successfully imported to EC2       ║')
   print('╚═════════════════════════════════════════════════════════╝\n')


   print(Fore.YELLOW +'➜ Run instance', end="\r")
   if instance_type == "":
      instance_type = "t2.micro"

   instances = ec2.run_instances(
                  ImageId=image_id,
                  MinCount=1,
                  MaxCount=1,
                  InstanceType= instance_type,
                  SecurityGroupIds=[group_name]
               )

   time.sleep(40)
   EC2_RESOURCE = boto3.resource('ec2', region_name=region_name)

   instances = EC2_RESOURCE.instances.all()

   for instance in instances:
      print('\n' + Fore.YELLOW + '⟪ EC2 instance %s" information ⟫' % instance.id)
      print(Fore.RED + '═'*60)
      print(Fore.BLUE + 'Instance state: ' + Fore.CYAN + '%s' % instance.state["Name"])
      print(Fore.BLUE + 'Instance AMI: ' + Fore.CYAN + '%s' % instance.image.id)
      print(Fore.BLUE + 'Instance platform: ' + Fore.CYAN + '%s' % instance.platform)
      print(Fore.BLUE + 'Instance type: ' + Fore.CYAN + '%s' % instance.instance_type)
      print(Fore.BLUE + 'Piblic IPv4 address: ' + Fore.CYAN + '%s' % instance.public_ip_address)
      print(Fore.RED + '═'*60)

if __name__ == "__main__":
   main()
