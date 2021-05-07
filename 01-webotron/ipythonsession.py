# coding: utf-8
import boto3
session = boto3.Session(profile_name='spark')
s3 = session.resource('s3')
ec2_client = session.client('ec2')
