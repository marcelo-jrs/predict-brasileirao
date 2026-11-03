import type { Metadata } from "next";
import Link from "next/link";

import { getAccuracy } from "@/lib/data";
import { formatNumber } from "@/lib/format";
import { getDict, isLang, type Lang } from "@/lib/i18n";
import { REPO_URL } from "@/lib/site";

export async function generateMetadata({ params }: PageProps<"/[lang]/how-it-works">): Promise<Metadata> {
  const { lang } = await params;
  return isLang(lang) ? { title: getDict(lang).nav.how } : {};
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-border bg-surface p-5">
      <h2 className="mb-2 text-lg font-semibold">{title}</h2>
      <div className="space-y-2 text-[15px] leading-relaxed text-foreground/90">{children}</div>
    </section>
  );
}

function Pt({ lang, marketGain }: { lang: Lang; marketGain: string }) {
  return (
    <>
      <Section title="1. A ideia em uma frase">
        <p>
          Ninguém sabe o resultado dos jogos que faltam, então damos <b>chances</b> para cada jogo e{" "}
          <b>jogamos o resto do campeonato 20 mil vezes no computador</b>. Se o Bahia termina no G6 em 16 mil dessas
          temporadas simuladas, a chance dele é 80%. É como a previsão do tempo: “80% de chance de chuva”.
        </p>
      </Section>
      <Section title="2. A chance de cada jogo">
        <p>Usamos três modelos, cada um aprende a “força” dos times de um jeito:</p>
        <ul className="list-disc space-y-1 pl-5">
          <li>
            <b>Elo</b> – como um ranking de videogame: todo time começa com 1500 pontos; quem ganha toma pontos de quem
            perde, e uma zebra rende mais pontos do que uma vitória esperada.
          </li>
          <li>
            <b>Poisson</b> – cada time tem uma força de <b>ataque</b> e de <b>defesa</b>. O modelo prevê quantos gols
            cada lado deve marcar e, daí, a chance de cada placar (2×0, 1×1…).
          </li>
          <li>
            <b>Mercado</b> – aprende a força dos times com as <b>odds das casas de apostas</b> nos jogos recentes. As
            casas sabem de lesões, desfalques e mudanças de técnico que os resultados ainda não mostram.
          </li>
        </ul>
        <p>Jogar em casa ajuda (o mandante vence ~48% dos jogos no Brasil, o visitante ~25%), e os três modelos levam isso em conta.</p>
      </Section>
      <Section title="3. A simulação">
        <p>
          Para cada jogo restante, “jogamos um dado viciado”: se o mandante tem 60% de chance, ele vence em ~60% das
          simulações. Somamos os pontos à tabela atual, aplicamos os critérios de desempate (pontos, vitórias, saldo,
          gols pró) e anotamos a posição final de cada time. Repetimos isso 20 mil vezes.
        </p>
        <p>
          Na página <Link href={`/${lang}/what-if/`} className="underline">E se…?</Link> essa mesma simulação roda no
          seu navegador, com os resultados que você escolher.
        </p>
      </Section>
      <Section title="4. Como sabemos se funciona?">
        <p>
          Fingimos estar no passado: escolhemos as configurações dos modelos com 2015–2018 e depois previmos cada jogo
          de 2019–2025 usando só o que se sabia antes dele. O modelo de Mercado foi o melhor ({marketGain} melhor que
          “chutar a média”), mas as odds finais das casas, publicadas minutos antes do jogo, ainda são melhores — elas
          são o nosso teto. Veja a página <Link href={`/${lang}/accuracy/`} className="underline">Precisão</Link>.
        </p>
      </Section>
      <Section title="5. Limitações">
        <ul className="list-disc space-y-1 pl-5">
          <li>Os modelos não sabem de lesões ou escalações (o de Mercado sabe um pouco, via odds).</li>
          <li>A força dos times fica fixa durante a simulação, então as chances tendem a ser um pouco confiantes demais.</li>
          <li>G6 = 6 primeiros da tabela; vagas extras por Copa do Brasil/Libertadores não são consideradas.</li>
        </ul>
        <p>
          Este é um projeto de estudo de ciência de dados. O código e os testes estão no{" "}
          <a href={REPO_URL} className="underline">GitHub</a>.
        </p>
      </Section>
    </>
  );
}

function En({ lang, marketGain }: { lang: Lang; marketGain: string }) {
  return (
    <>
      <Section title="1. The idea in one sentence">
        <p>
          Nobody knows the results of the remaining games, so we give each game <b>chances</b> and{" "}
          <b>play the rest of the season 20,000 times on a computer</b>. If Bahia finishes in the top 6 in 16,000 of
          those simulated seasons, its chance is 80%. Just like a weather forecast: “80% chance of rain”.
        </p>
      </Section>
      <Section title="2. The chances of each game">
        <p>We use three models, each learning team “strength” in a different way:</p>
        <ul className="list-disc space-y-1 pl-5">
          <li>
            <b>Elo</b> – like an online game ranking: every team starts at 1500 points; the winner takes points from the
            loser, and an upset is worth more than an expected win.
          </li>
          <li>
            <b>Poisson</b> – each team has an <b>attack</b> and a <b>defence</b> strength. The model predicts how many
            goals each side should score and, from that, the chance of every score (2–0, 1–1…).
          </li>
          <li>
            <b>Market</b> – learns team strength from <b>bookmakers&apos; odds</b> for recent games. Bookmakers know about
            injuries, suspensions and coaching changes that results don&apos;t show yet.
          </li>
        </ul>
        <p>Home advantage is real (home teams win ~48% of games in Brazil, away teams ~25%) and all three models account for it.</p>
      </Section>
      <Section title="3. The simulation">
        <p>
          For every remaining game we “roll a weighted die”: if the home team has a 60% chance, it wins in ~60% of the
          simulations. We add the points to the current table, apply the tiebreakers (points, wins, goal difference,
          goals scored) and record each team&apos;s final position. Then we repeat it 20,000 times.
        </p>
        <p>
          On the <Link href={`/${lang}/what-if/`} className="underline">What if…?</Link> page the same simulation runs in
          your browser, with the results you pick.
        </p>
      </Section>
      <Section title="4. How do we know it works?">
        <p>
          We pretend to be in the past: model settings are chosen using 2015–2018, then every game of 2019–2025 is
          predicted using only what was known before it. The Market model came out best ({marketGain} better than
          “always guess the average”), but bookmakers&apos; closing odds, published minutes before kick-off, are better
          still — they&apos;re our ceiling. See the <Link href={`/${lang}/accuracy/`} className="underline">Accuracy</Link>{" "}
          page.
        </p>
      </Section>
      <Section title="5. Limitations">
        <ul className="list-disc space-y-1 pl-5">
          <li>The models don&apos;t know about injuries or line-ups (the Market model does a little, through the odds).</li>
          <li>Team strength is frozen during a simulation, so the chances tend to be slightly overconfident.</li>
          <li>Top 6 = first six in the table; extra places from cup winners are ignored.</li>
        </ul>
        <p>
          This is a data-science learning project. The code and the tests are on{" "}
          <a href={REPO_URL} className="underline">GitHub</a>.
        </p>
      </Section>
    </>
  );
}

export default async function HowItWorksPage({ params }: PageProps<"/[lang]/how-it-works">) {
  const { lang } = await params;
  if (!isLang(lang)) return null;
  const t = getDict(lang);
  const board = getAccuracy().leaderboard;
  const baseline = board.find((m) => m.id === "baseline")!.log_loss;
  const market = board.find((m) => m.id === "market")!.log_loss;
  const marketGain = `${formatNumber((100 * (baseline - market)) / baseline, lang, 1)}%`;

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <h1 className="text-2xl font-bold sm:text-3xl">{t.nav.how}</h1>
      {lang === "pt" ? <Pt lang={lang} marketGain={marketGain} /> : <En lang={lang} marketGain={marketGain} />}
    </div>
  );
}
