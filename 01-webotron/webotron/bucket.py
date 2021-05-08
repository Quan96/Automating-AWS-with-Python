#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Classes for AWS S3 Buckets."""

import mimetypes
from pathlib import Path

from botocore.exceptions import ClientError


class BucketManager:
    """Manage an AWS S3 Bucket."""
    def __init__(self, session):
        self.session = session
        self.s3 = self.session.resource('s3')

    def all_buckets(self):
        """Get an iterator for all buckets."""
        return self.s3.buckets.all()

    def all_objects(self, bucket_name):
        """Get an iterator for all objects in bucket"""
        return self.s3.Bucket(bucket_name).objects.all()

    def init_bucket(self, bucket_name):
        """Create new bucket, or return existing one by name."""
        s3_bucket = None
        try:
            s3_bucket = self.s3.create_bucket(Bucket=bucket_name,
                                            CreateBucketConfiguration=
                                                {'LocationConstraint': self.session.region_name}
                                        )
        except ClientError as error:
            if error.response['Error']['Code'] == "BucketAlreadyOwnedByYou":
                s3_bucket = self.s3.Bucket(bucket_name)
            else:
                raise error

        return s3_bucket

    def set_policy(self, bucket):
        """Set bucket policy"""
        policy = """{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": [
                        "s3:GetObject"
                    ],
                    "Resource": [
                        "arn:aws:s3:::%s/*"
                    ]
                }
            ]
            }""" % bucket.name
        policy = policy.strip()
        pol = bucket.Policy()
        pol.put(Policy=policy)

    def configure_website(self, bucket):
        """Configure the website hosting for AWS S3 bucket"""
        website = bucket.Website()
        website.put(WebsiteConfiguration={
            'ErrorDocument': {
                'Key': 'error.html'
            },
            'IndexDocument': {
                'Suffix': 'index.html'
            }
        })

    @staticmethod
    def upload_file(bucket, path, key):
        """Upload files to AWS S3 bucket."""

        content_type = mimetypes.guess_type(key)[0] or 'text/plains'
        return bucket.upload_file(
            path,
            key,
            ExtraArgs={
                'ContentType': content_type
            }
        )

    def sync(self, pathname, bucket_name):

        bucket = self.s3.Bucket(bucket_name)

        root = Path(pathname).expanduser().resolve()
        
        def handle_directory(target):
            for path in target.iterdir():
                if path.is_dir():
                    handle_directory(path)
                if path.is_file():
                    self.upload_file(bucket, str(path), str(path.relative_to(root)))

        handle_directory(root)
