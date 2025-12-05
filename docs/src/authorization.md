# Authorization
Authorization is how Lif Platforms ensures users can only do what they have permission to do. We do this through a roles and permissions system. On this page, we will explain how we use roles and permissions to ensure resources are protected and users only access what they are intended to access.

## Roles
> [!NOTE]
> Lif Platforms may be moving away from roles in favor of permission groups. To avoid future issues, it's best to avoid using roles in favor of permission nodes. These are explained on this page.

Auth Server uses roles to define what a user can and cannot access. For example, to access the Lif Mod Site, you will need to have the "MODERATOR" role. Lif Platforms also have a special "SUSPENDED" role. This is how we suspend or ban accounts that have violated our [Terms of Service](https://lifplatforms.com/legal/terms-of-service).

## Permission Nodes
Auth Server also used permission nodes to define what users can and can't access. Permission nodes are defined in two main parts.

1. **Namespace:** This is the group of actions being accessed. Think of it like a folder for permission nodes.
2. **Resource:** This is the action being taken. Examples include viewing, modifying, or deleting a recourse.

An example of a permission node would be something like `mail.send`. In this case, "mail" is our namespace and "send" is our recourse or action. Referring to the example again, "mail" is the group of actions we want to take. Other actions may include view, read, or write. In this case, "send" is the action we are taking.

## Access Control
> [!IMPORTANT]
> Lif Platforms is moving away from this system in favor of our new API credentials system.

Access control allows services to gain access to sensitive information if needed and perform high risk actions. Examples include getting sensitive account details and sending emails to users. This system is managed though the `access-control.yml` file. This file contains a list of access keys and their permission nodes. Example:

```yml
hfkr-heis-nvte-prmt:
    - Node1
    - Node2
    - Node3
```