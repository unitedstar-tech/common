resource "aws_vpc" "vpc" {
    cidr_block = "192.168.0.0/16"
    tags = {
        Name = "Terraform"
    }
}
resource "aws_internet_gateway" "igw" {
    vpc_id = aws_vpc.vpc.id
}
resource "aws_route" "public_route" {
    route_table_id = aws_vpc.vpc.main_route_table_id
    destination_cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
}
resource "aws_subnet" "public1" {
    vpc_id = aws_vpc.vpc.id
    cidr_block = "192.168.0.0/24"
    availability_zone = "ap-northeast-1a"
    map_public_ip_on_launch = true
    tags = {
        Name = "Public A"
    }
}
resource "aws_subnet" "public2" {
    vpc_id = aws_vpc.vpc.id
    cidr_block = "192.168.64.0/24"
    availability_zone = "ap-northeast-1c"
    map_public_ip_on_launch = true
    tags = {
        Name = "Public C"
    }
}
resource "aws_route_table_association" "public_route_asspciation1" {
    subnet_id = aws_subnet.public1.id
    route_table_id = aws_vpc.vpc.main_route_table_id
}
resource "aws_route_table_association" "public_route_asspciation2" {
    subnet_id = aws_subnet.public2.id
    route_table_id = aws_vpc.vpc.main_route_table_id
}
resource "aws_route_table" "private_route_table" {
    vpc_id = aws_vpc.vpc.id
}
resource "aws_subnet" "private1" {
    vpc_id = aws_vpc.vpc.id
    cidr_block = "192.168.128.0/24"
    availability_zone = "ap-northeast-1a"
    tags = {
        Name = "Private A"
    }
 }
 resource "aws_subnet" "private2" {
    vpc_id = aws_vpc.vpc.id
    cidr_block = "192.168.192.0/24"
    availability_zone = "ap-northeast-1c"
    tags = {
        Name = "Private C"
    }
 }
resource "aws_route_table_association" "private_route_asspciation1" {
    subnet_id = aws_subnet.private1.id
    route_table_id = aws_route_table.private_route_table.id
}
resource "aws_route_table_association" "private_route_asspciation2" {
    subnet_id = aws_subnet.private2.id
    route_table_id = aws_route_table.private_route_table.id
}
resource "aws_security_group" "sg" {
    name = "Self"
    vpc_id = aws_vpc.vpc.id
    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }
    ingress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        self = true
    }
}