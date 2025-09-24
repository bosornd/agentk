import 'package:flutter/material.dart';
import 'chat_page.dart';
import 'config.dart';
import 'session_info.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

class ChatMessage {
  final String text;
  final bool isUser;
  final Map<String, dynamic>? card;
  ChatMessage({required this.text, required this.isUser, this.card});
}

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Demo',
      theme: ThemeData(
        // This is the theme of your application.
        //
        // TRY THIS: Try running your application with "flutter run". You'll see
        // the application has a purple toolbar. Then, without quitting the app,
        // try changing the seedColor in the colorScheme below to Colors.green
        // and then invoke "hot reload" (save your changes or press the "hot
        // reload" button in a Flutter-supported IDE, or press "r" if you used
        // the command line to start the app).
        //
        // Notice that the counter didn't reset back to zero; the application
        // state is not lost during the reload. To reset the state, use hot
        // restart instead.
        //
        // This works for code too, not just values: Most code changes can be
        // tested with just a hot reload.
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
      ),
      home: const MyHomePage(title: 'Flutter Demo Home Page'),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title});
  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  List<SessionInfo> sessions = [];
  Map<String, List<ChatMessage>> sessionMessages = {};
  Map<String, Map<String, dynamic>> sessionStates = {};
  Map<String, dynamic> sessionInfoWindows = {};
  Map<String, Map<String, dynamic>?> sessionWindows = {};
  int? selectedSessionIndex;

  Future<void> _addSession() async {
    final sessionTitle = 'Session ${sessions.length + 1}';
    String sessionId = '';
    String? greetingText;
    try {
      final response = await http.post(
        Uri.parse('${AppConfig.serverUrl}/session'),
      );
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        sessionId = data['session_id'] ?? '';
      }
    } catch (e) {
      sessionId = '';
    }
    if (sessionId.isEmpty) return;

    // 세션 생성 후 greetings 메시지 요청 (/chat, 사용자 메시지 없이)
    try {
      final greetResp = await http.post(
        Uri.parse('${AppConfig.serverUrl}/chat'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'session_id': sessionId, 'text': ''}),
      );
      if (greetResp.statusCode == 200) {
        final greetData = json.decode(greetResp.body);
        greetingText = greetData['text'] ?? null;
      }
    } catch (e) {
      greetingText = null;
    }

    setState(() {
      sessions.add(SessionInfo(title: sessionTitle, sessionId: sessionId));
      sessionMessages[sessionId] =
          greetingText != null && greetingText.isNotEmpty
          ? [ChatMessage(text: greetingText, isUser: false)]
          : [];
      selectedSessionIndex = sessions.length - 1;
    });
    _openChatPage(sessionTitle, sessionId);
  }

  void _removeSession(int index) {
    setState(() {
      if (selectedSessionIndex == index) selectedSessionIndex = null;
      sessionMessages.remove(sessions[index].sessionId);
      sessions.removeAt(index);
    });
  }

  void _selectSession(int index) {
    setState(() {
      selectedSessionIndex = index;
    });
    final session = sessions[index];
    _openChatPage(session.title, session.sessionId);
  }

  void _openChatPage(String sessionTitle, String sessionId) async {
    final result = await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => ChatPage(
          sessionName: sessionTitle,
          sessionId: sessionId,
          initialMessages: List<ChatMessage>.from(
            sessionMessages[sessionId] ?? [],
          ),
          savedState: sessionStates[sessionId],
          savedInfoWindow: sessionInfoWindows[sessionId],
          savedWindow: sessionWindows[sessionId],
        ),
      ),
    );
    if (result != null && result is Map<String, dynamic>) {
      setState(() {
        sessionMessages[sessionId] = List<ChatMessage>.from(
          result['messages'] ?? [],
        );
        sessionStates[sessionId] = Map<String, dynamic>.from(
          result['state'] ?? {},
        );
        sessionInfoWindows[sessionId] = result['infoWindow'];
        sessionWindows[sessionId] = result['window'];
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Chatbot 세션 관리')),
      body: sessions.isEmpty
          ? const Center(child: Text('세션이 없습니다.'))
          : ListView.builder(
              itemCount: sessions.length,
              itemBuilder: (context, index) {
                final isSelected = selectedSessionIndex == index;
                final session = sessions[index];
                return Dismissible(
                  key: Key(session.sessionId),
                  direction: DismissDirection.endToStart,
                  background: Container(
                    color: Colors.red,
                    alignment: Alignment.centerRight,
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    child: const Icon(Icons.delete, color: Colors.white),
                  ),
                  onDismissed: (direction) {
                    _removeSession(index);
                  },
                  child: ListTile(
                    title: Text(session.title),
                    selected: isSelected,
                    onTap: () => _selectSession(index),
                  ),
                );
              },
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: _addSession,
        tooltip: '새 세션 생성',
        child: const Icon(Icons.add),
      ),
    );
  }
}
