import styled from "@emotion/styled";
import Checkbox from "@mui/material/Checkbox";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormGroup from "@mui/material/FormGroup";
import { forwardRef, useCallback, useImperativeHandle, useState, useMemo, useContext } from "react";
import { ScrollableCollapseableFilterSection } from "src/pages/RunSearch/filters/CollapseableFilterSection";
import { ResettableHandle } from "src/component/common";
import theme from "src/theme/new";
import { useUsersList } from "src/hooks/userHooks";
import UserContext from "src/context/UserContext";
import NameTag from "src/component/NameTag";


const Container = styled.div`
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    column-gap: ${theme.spacing(2)};
    row-gap: ${theme.spacing(2)};
    margin-top: -${theme.spacing(2)};
    margin-bottom: 2px;

    overflow-y: auto;
`;

const StyledFormControlLabel = styled(FormControlLabel)`
    height: 50px;
    margin-left: ${theme.spacing(2.9)};
`;

interface OwnersFilterSectionProps {
    onFiltersChanged?: (filters: string[]) => void;
}

const OwnersFilterSection = forwardRef<ResettableHandle, OwnersFilterSectionProps>((props, ref) => {
    const { onFiltersChanged } = props;
    const [filters, setFilters] = useState<Set<string>>(() => new Set());

    const { users } = useUsersList();
    const { user: currentUser } = useContext(UserContext);

    const otherUsers = useMemo(() => {
        if (!users || users.length === 0) {
            return undefined;
        }
        return users!.filter((user) => user.id !== currentUser?.id);

    }, [currentUser, users]);

    const toogleFilter = useCallback((filter: string, checked: boolean) => {
        let newFilters: any;
        setFilters((filters) => {
            if (checked) {
                filters.add(filter);
            } else {
                filters.delete(filter);
            }
            newFilters = new Set(filters);
            onFiltersChanged?.(Array.from(newFilters));
            return newFilters;
        });

    }, [onFiltersChanged, setFilters]);

    useImperativeHandle(ref, () => ({
        reset: () => {
            setFilters(new Set());
        }
    }));

    return <ScrollableCollapseableFilterSection title={"Owner"} >
        <Container>
            <FormGroup>
                <StyledFormControlLabel control={<Checkbox
                    checked={filters.has(currentUser!.id)}
                    onChange={(event) => toogleFilter(currentUser!.id, event.target.checked)} />} label="Your runs"
                />
                {!!otherUsers && otherUsers.map(
                    (user, index) =>
                        <StyledFormControlLabel key={index} control={<Checkbox
                            onChange={(event) => toogleFilter(user.id, event.target.checked)} />}
                        label={<NameTag firstName={user.first_name} lastName={user.last_name} />}
                        checked={filters.has(user.id)} />
                )}
            </FormGroup>
        </Container>
    </ScrollableCollapseableFilterSection>;
})

export default OwnersFilterSection;
