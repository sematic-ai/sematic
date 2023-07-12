import { Checkbox, DialogContent, DialogContentText, DialogTitle, FormControlLabel, FormGroup } from "@mui/material";
import Button from "@mui/material/Button/Button";
import Dialog from "@mui/material/Dialog/Dialog";
import DialogActions from "@mui/material/DialogActions/DialogActions";
import Link from "@mui/material/Link/Link";
import { styled } from "@mui/system";
import { useAtom } from "jotai";
import { atomWithStorage } from "jotai/utils";
import React, { forwardRef, useCallback, useImperativeHandle, useMemo, useRef, useState } from "react";
import { applyPostHogOptOutSetting, optOutStorageKey } from "src/utils/postHogManager";

const PageFooterContainer = styled("div", {
    shouldForwardProp: () => true
})`
  position: fixed;
  bottom: 0;
  right: 0;
  width: fit-content;
`;

const StyledNoticeText = styled("div")`
  padding: ${({ theme }: any) => theme.spacing(2)};
  cursor: pointer;
  color: ${({ theme }) => theme.palette.grey[400]}
`;

const optOutSetting = atomWithStorage<boolean | null>(optOutStorageKey, null);

export interface TrackingNoticeDialogRefType {
    setOpen: (open: boolean) => void;
}

const TrackingNoticeDialog = forwardRef<TrackingNoticeDialogRefType>(function TrackingNoticeDialog(_, ref) {
    const [open, setOpen] = useState(false);

    const handleClose = () => {
        setOpen(false);
    };

    useImperativeHandle(ref, () => ({
        setOpen
    }));

    const [attempt, setAttempt] = useState<number>(0);
    const [optOut, setOptOut] = useAtom(optOutSetting);

    const hasUserOptout = useMemo(() => {
        if (optOut === null) {
            if (!!(navigator as unknown as any)["globalPrivacyControl"]) {
                return true;
            }
        } else {
            return optOut;
        }
        return false;
    }, [attempt, optOut]); // eslint-disable-line react-hooks/exhaustive-deps

    const flipOptOutState = useCallback(() => {
        const shouldUserOptout = !hasUserOptout;
        setOptOut(shouldUserOptout);
        applyPostHogOptOutSetting(shouldUserOptout);
        setAttempt(value => value + 1);
    }, [hasUserOptout, setOptOut]);

    return <Dialog
        open={open}
        onClose={handleClose}
        aria-labelledby="scroll-dialog-title"
        aria-describedby="scroll-dialog-description"
    >
        <DialogTitle id="scroll-dialog-title">Anonymous Usage Tracking Policy</DialogTitle>
        <DialogContent>
            <DialogContentText
                id="scroll-dialog-description"
                component={"div"}
            >
                <p>In order for Sematic to continuously improve its user experience, and measure the size of the community, minimal anonymous analytics are collected. </p>
                <p>Sematic counts unique sessions of this web app in a completely anonymous way. No information identifying the user or the host machine are collected. The Sematic backend does not track anything.</p>
                <p>If you want to opt-out, simply uncheck the box below.</p>
            </DialogContentText>
            <FormGroup>
                <FormControlLabel control={<Checkbox checked={!hasUserOptout}
                    onClick={flipOptOutState} />}
                label="I am ok with Sematic collecting anonymous usage analytics." />
            </FormGroup>
            <DialogContentText>
                If you have any questions, reach out to us on
                <Link
                    href="https://discord.gg/4KZJ6kYVax"
                    underline="none"
                    target="_blank"
                > Discord </Link> or at&nbsp;
                <Link href="mailto:support@sematic.dev">support@sematic.dev</Link>.
            </DialogContentText>
        </DialogContent>
        <DialogActions>
            <Button onClick={handleClose}>Ok</Button>
        </DialogActions>
    </Dialog>
});

interface TrackingNoticeProps {
    sx?: React.ComponentProps<typeof PageFooterContainer>["sx"];
    children?: React.ReactNode;
}

export function TrackingNoticeFooter({ sx }: TrackingNoticeProps) {
    const ref = useRef<TrackingNoticeDialogRefType>(null);

    return <PageFooterContainer sx={sx}>
        <StyledNoticeText onClick={() => ref.current?.setOpen(true)}>
            Anonymous Usage Tracking Policy
        </StyledNoticeText>
        <TrackingNoticeDialog ref={ref} />
    </PageFooterContainer>
}

interface TrackingNoticeButtonProps extends TrackingNoticeProps {
    ref?: React.Ref<TrackingNoticeDialogRefType>;
}

export const TrackingNoticeButton = forwardRef<TrackingNoticeDialogRefType, TrackingNoticeButtonProps>(
    function TrackingNoticeButton(props, ref) {
        const { children } = props;
        return <>
            {children}
            <TrackingNoticeDialog ref={ref} />
        </>
    });
