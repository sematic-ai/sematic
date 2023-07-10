import { User } from "src/Models";
import NameTag from "src/component/NameTag";
import UserAvatar from "src/component/UserAvatar";
import { getUserInitials } from "src/utils/string";
import styled from "@emotion/styled";
import theme from "src/theme/new";

const StyledContainer = styled.div`
    display: inline-flex;
    & > :first-of-type {
        margin-right: ${theme.spacing(1)};
    }
`;

interface OwnerColumnProps {
    user: User | null;
}

export default function OwnerColumn(props: OwnerColumnProps) {
    const { user } = props;

    if (!user) return null;

    return <StyledContainer>
        <UserAvatar initials={getUserInitials(user?.first_name, user?.last_name, user?.email)}
            hoverText={user?.first_name || user?.email} avatarUrl={user?.avatar_url} />
        <NameTag firstName={user.first_name} lastName={user.last_name} />
    </StyledContainer>;
}
