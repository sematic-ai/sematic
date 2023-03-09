import { Avatar, AvatarProps } from "@mui/material";
import { User } from "../Models";

function userInitials(user: User) {
  let initials = "";

  if (user.first_name) {
    initials += user.first_name[0];
    if (user.last_name) {
      initials += user.last_name[0];
    }
  } else {
    initials += user.email[0];
  }

  return initials;
}

interface UserAvatarProps extends AvatarProps {
  user: User;
}

export default function UserAvatar(props: UserAvatarProps) {
  const { user, ...other } = props;

  return (
    <Avatar
      alt={user.first_name || user.email}
      src={user.avatar_url || undefined}
      {...other}
    >
      {userInitials(user)}
    </Avatar>
  );
}
