const DEFAULT_CHAT_TITLE = "新しいチャット";
const MESSAGE_IN_PROGRESS = "少々お待ちください...";
const MESSAGE_ERROR = "エラーが発生したため回答できませんでした。";

Vue.use(VueMarkdown);
const vue = new Vue({
    el: '#app',
    data: {
        userMessage: "",
        talks: [],
        selectedTalkIndex: 0,
        receiving: false,
        maxTalkCount: 20,
        textAreaRows: 1,
    },
    watch: {
        userMessage: function () {
            // 入力されているメッセージ内の改行コード数に応じて入力フォームの行数を設定する
            const match = this.userMessage.match(/\n/g);
            this.textAreaRows = match ? match.length + 1 : 1;
        },
        selectedTalkIndex: function () {
            this.refreshSyntaxHighlighting(); // コードをシンタックスハイライトする
        },
    },
    async mounted() {
        await this.listTalks();
        this.refreshSyntaxHighlighting(); // コードをシンタックスハイライトする
        if (this.talks.length == 0)
            this.addTalk();
    },
    methods: {
        listTalks: async function () {
            const resp = await axios.get("talks");
            this.talks = resp.data;
        },
        addTalk: async function () {
            this.selectedTalkIndex = -1;
            const resp = await axios.post("talks", { title: DEFAULT_CHAT_TITLE });
            const talk = resp.data;
            this.talks.push(talk);
            this.selectedTalkIndex = this.talks.length - 1;
        },
        deleteTalk: async function (talkIndex) {
            // サーバ側のチャットデータを削除する
            axios.delete(`/talks/${this.talks[talkIndex].id}`);

            // チャット表示を削除する
            this.talks.splice(talkIndex, 1);
            this.selectedTalkIndex--;
            if (this.selectedTalkIndex < 0)
                this.selectedTalkIndex = 0;
            if (this.talks.length == 0)
                await this.addTalk();
        },
        sendUserMessage: async function () {
            const talk = this.talks[this.selectedTalkIndex];
            const message = this.userMessage.trim();
            if (this.receiving || !message) return;

            // 画面に入力したメッセージを表示する
            talk.messages.push({ role: "user", content: message });
            talk.messages.push({ role: "assistant", content: MESSAGE_IN_PROGRESS });
            this.receiving = true;
            this.userMessage = "";
            this.textAreaRows = 1;

            // サーバ側にメッセージを送信する
            const resp = await fetch(`/talks/${talk.id}/message`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message }),
            });

            // サーバ側でエラーが発生した場合の処理
            if (!resp.ok) {
                talk.messages[talk.messages.length - 1].content = MESSAGE_ERROR;
                this.receiving = false;
                return;
            }

            // サーバ側からのメッセージを受信する(ストリーミング形式)
            const reader = resp.body.getReader();
            let runningText = "";
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const text = new TextDecoder("utf-8").decode(value);
                text.split("\n").forEach((t) => {
                    if (!t) return;
                    runningText += t;
                    const result = JSON.parse(runningText);
                    if (result.content)
                        talk.messages[talk.messages.length - 1].content = result.content
                    runningText = "";
                });
            }
            this.receiving = false;
            this.refreshSyntaxHighlighting(); // コードをシンタックスハイライトする

            // 初回のメッセージ送信時かつタイトルが変更されていない場合にタイトルを自動生成する
            if (talk.messages.length <= 3 && talk.title == DEFAULT_CHAT_TITLE) {
                const resp = await axios.post(`/talk/${talk.id}/title/gen`);
                talk.title = resp.data;
            }
        },
        updateTalkTitle: async function () {
            const talk = this.talks[this.selectedTalkIndex];
            const title = talk.title.trim();
            await axios.put(`/talk/${talk.id}/title`, { title });
        },
        refreshSyntaxHighlighting: function () {
            setTimeout(() => { hljs.highlightAll(); }, 1);
        },
    }
});
