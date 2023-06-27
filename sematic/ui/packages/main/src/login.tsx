import Alert from "@mui/material/Alert/Alert";
import Paper from "@mui/material/Paper/Paper";
import { CredentialResponse, GoogleLogin, GoogleOAuthProvider } from "@react-oauth/google";
import { User } from "@sematic/common/src/Models";
import AppContext from "@sematic/common/src/context/appContext";
import { useAppContext } from "@sematic/common/src/hooks/appHooks";
import { useHttpClient } from "@sematic/common/src/hooks/httpHooks";
import { ExtractContextType } from "@sematic/common/src/utils/typings";
import { useAtom } from "jotai";
import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import logo from "src/Fox.png";
import { GoogleLoginPayload } from "src/Payloads";
import { userAtom } from "src/hooks/appHooks";

interface GoogleLoginComponentProps {
    setUser: (user: User) => void;
    setError: (error: Error | undefined) => void;
    authProviderDetail: Exclude<ExtractContextType<typeof AppContext>[
        "authProviderDetails"]["google"], undefined>,
}

function GoogleLoginComponent({
    setUser, setError, authProviderDetail
}: GoogleLoginComponentProps) {

    const navigate = useNavigate();

    const { fetch } = useHttpClient();

    const onGoogleLoginSuccess = useCallback(
        async (credentialResponse: CredentialResponse) => {
            try {
                const payload: GoogleLoginPayload = await (await fetch({
                    url: "/login/google",
                    method: "POST",
                    body: {
                        token: credentialResponse.credential,
                    },
                })).json();
                setError(undefined);
                setUser(payload.user);
                navigate(-1);
            } catch (error) {
                setError(error as Error);
            }
        }, [setError, setUser, navigate, fetch]);

    return <GoogleOAuthProvider
        clientId={authProviderDetail.GOOGLE_OAUTH_CLIENT_ID}
    >
        <GoogleLogin
            text="signin_with"
            logo_alignment="center"
            onSuccess={onGoogleLoginSuccess}
            onError={() => {
                setError(Error("Unauthorized user"));
            }}
        />
    </GoogleOAuthProvider>
}


export default function LoginPage() {
    const [error, setError] = useState<Error | undefined>(undefined);
    const { authProviderDetails } = useAppContext()
    const [, setUser] = useAtom(userAtom);

    return <Paper
        sx={{
            width: 200,
            p: 5,
            textAlign: "center",
            top: "50%",
            left: "50%",
            position: "absolute",
            transform: "translateY(-50%) translateX(-50%)",
        }}
        variant="outlined"
    >
        <img
            src={logo}
            width="50px"
            alt="Sematic logo"
            style={{ marginBottom: "30px" }}
        />

        {error ? <Alert severity="error">{error.message}</Alert> : <></>}

        {!error && authProviderDetails.google &&
        <GoogleLoginComponent setUser={setUser}
            authProviderDetail={authProviderDetails.google!} setError={setError} />
        }
        {!error && authProviderDetails.github &&
        <>{
            // TODO: Add github login
        }</>
        }
    </Paper>;
}