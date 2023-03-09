import { abbreviatedUserName, sha1 } from "../utils";
import user from "@sematic/ui-test/fixtures/user";

describe('sha1', () => {
    it("should calculate sha1 value from string", async () => {
        expect(await sha1("localhost")).to.equal("334389048b872a533002b34d73f8c29fd09efc50");
        expect(await sha1("127.0.0.1")).to.equal("4b84b15bff6ee5796152495a230e45e3d7e947d9");
    });
});

describe('abbreviatedUserName()', () => {
    it("should generate abbreviated user name with User data", () => {
        expect(abbreviatedUserName(user)).to.equal("Grace H.");
    });
    it("should return empty string when the parameter is not provided", () => {
        expect(abbreviatedUserName(null)).to.equal("");
    });
});